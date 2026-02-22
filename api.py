import os
import json
import re
from typing import TypedDict, List, Literal, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langgraph.graph import StateGraph, END
from google import genai
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from adapters.universal_adapter import UniversalSearchAdapter
from core.ports import Product

# --- 1. SETUP & CONFIG ---
load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


MODEL_NAME = "gemini-flash-latest"

if not RAPIDAPI_KEY or not GEMINI_API_KEY:
    raise ValueError("Missing API Keys in .env file")

client = genai.Client(api_key=GEMINI_API_KEY)
search_tool = UniversalSearchAdapter(RAPIDAPI_KEY)

# --- 2. FASTAPI APP & MODELS ---
app = FastAPI(title="AI Shopping Agent API")

# Allow frontend apps to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allows all origins ( need to change for production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserRequest(BaseModel):
    query: str

class AgentResponse(BaseModel):
    response: str
    products: Optional[List[dict]] = []

# --- 3. AGENT STATE ---
class AgentState(TypedDict):
    user_input: str
    search_params: dict
    products: List[Product]
    final_response: str

# --- 4. GRAPH NODES  ---

def node_understand(state: AgentState):
    print(f"🧠 [Understand] Parsing: {state['user_input']}")
    
    prompt = f"""
    Analyze this request: "{state['user_input']}"
    
    Extract into JSON:
    - query: (str)
    - max_price: (int, default 0)
    - min_price: (int, default 0)
    - min_reviews: (int) Default 0.
    - sort_by: 'BEST_MATCH', 'LOWEST_PRICE', 'TOP_RATED'
    
    Example: {{"query": "mouse", "max_price": 2000, "sort_by": "TOP_RATED"}}
    """
    
    try:
        response = client.models.generate_content(
            model=MODEL_NAME, 
            contents=prompt
        )
        text = response.text.strip()
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            params = json.loads(match.group())
        else:
            params = {"query": state["user_input"]}
            
        print(f"   -> Extracted: {params}")
    except Exception as e:
        print(f"⚠️ Understanding failed: {e}")
        params = {"query": state['user_input']}
    
    return {"search_params": params}

def node_search(state: AgentState):
    p = state.get("search_params", {})
    if not p.get("query"): return {"products": []}
    
    results = search_tool.search_products(
        query=p.get("query"),
        max_price=p.get("max_price"),
        min_price=p.get("min_price", 0),
        sort_by=p.get("sort_by", "BEST_MATCH"),
        min_reviews=p.get("min_reviews", 0),
        condition="ANY" # Defaulting condition
    )
    
    return {"products": results}

def node_respond(state: AgentState):
    products = state.get("products", [])
    if not products:
        return {"final_response": "I couldn't find any items matching that request."}

    p = state.get("search_params", {})
    sort_by = p.get("sort_by", "BEST_MATCH")

    # Manual Sorting 
    if sort_by == "LOWEST_PRICE":
        products.sort(key=lambda x: x.price)
    elif sort_by == "TOP_RATED":
        products.sort(key=lambda x: (x.rating, x.reviews), reverse=True)

    top_products = products[:5] # Keep top 5 for context

    summary_prompt = f"""
    User Request: "{state['user_input']}"
    Products Found:
    {[f"{p.title} - ₹{p.price}" for p in top_products]}

    Write a helpful recommendation explaining why these are good options.
    Keep it concise.
    """

    try:
        res = client.models.generate_content(
            model=MODEL_NAME,
            contents=summary_prompt
        )
        explanation = res.text.strip()
    except:
        explanation = "Here are the best options I found:"

    # Formatting the markdown response
    formatted_output = explanation + "\n\n"
    for p in top_products[:3]: # Show top 3 details
        formatted_output += (
            f"### {p.title}\n"
            f"**Price:** ₹{p.price}\n"
            f"**Rating:** {p.rating}★ ({p.reviews} reviews)\n"
            f"**Store:** {p.source}\n"
            f"![Image]({p.image_url})\n"
            f"[Buy Now]({p.link})\n\n"
        )

    return {"final_response": formatted_output}

# --- 5. BUILD GRAPH ---
def decide(state):
    return "respond" if not state["search_params"].get("query") else "search"

workflow = StateGraph(AgentState)
workflow.add_node("understand", node_understand)
workflow.add_node("search", node_search)
workflow.add_node("respond", node_respond)

workflow.set_entry_point("understand")
workflow.add_conditional_edges("understand", decide, {"search": "search", "respond": "respond"})
workflow.add_edge("search", "respond")
workflow.add_edge("respond", END)

# Compile the graph
agent_app = workflow.compile()

# --- 6. API ENDPOINT ---
@app.post("/chat", response_model=AgentResponse)
async def chat(request: UserRequest):
    """
    Endpoint to interact with the Shopping Agent.
    """
    try:
        # Run the LangGraph agent
        inputs = {"user_input": request.query}
        result = agent_app.invoke(inputs)
        
        products_data = [
            {
                "title": p.title,
                "price": p.price,
                "link": p.link,
                "image": p.image_url,
                "rating": p.rating,
                "reviews": p.reviews
            } 
            for p in result.get("products", [])[:3]
        ]
        
        return AgentResponse(
            response=result["final_response"],
            products=products_data
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting FastAPI Shopping Agent...")
    uvicorn.run(app, host="0.0.0.0", port=8000)



    