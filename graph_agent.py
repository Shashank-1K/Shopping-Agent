import os
import json
from typing import TypedDict, List, Literal
from langgraph.graph import StateGraph, END
from google import genai
from adapters.universal_adapter import UniversalSearchAdapter
from dotenv import load_dotenv

load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)
search_tool = UniversalSearchAdapter(RAPIDAPI_KEY)

class AgentState(TypedDict):
    user_input: str.\venv\Scripts\python.exe -m pip list
    search_params: dict
    products: List
    final_response: str

def node_understand(state: AgentState):
    print(f"🧠 [Understand] Parsing: {state['user_input']}")
    
    prompt = f"""
    Analyze this request: "{state['user_input']}"
    
    Extract into JSON:
    - query: (str)
    - max_price: (int, default 0)
    - min_price: (int, default 0)
    - min_reviews: (int) Extract if user asks for "popular", "trusted", or specific number. Default 0.
    - sort_by: 'BEST_MATCH' (default), 'LOWEST_PRICE', 'TOP_RATED'
    
    Example: "Popular gaming mouse under 2000" 
    Result: {{"query": "gaming mouse", "max_price": 2000, "min_reviews": 100, "sort_by": "TOP_RATED"}}
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-flash-latest', 
            contents=prompt
        )

        text = response.text.strip()

        # Extract JSON 
        import re
        match = re.search(r"\{.*\}", text, re.DOTALL)

        if match:
            try:
                params = json.loads(match.group())
            except json.JSONDecodeError:
                params = {"query": state["user_input"]}
        else:
            params = {"query": state["user_input"]}



        print(f"   -> Extracted: {params}")
    except:
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
        min_reviews=p.get("min_reviews", 0)
    )
    
    return {"products": results}

def node_respond(state: AgentState):
    products = state.get("products", [])
    if not products:
        return {"final_response": "I couldn't find any Amazon/Flipkart items matching that."}

    p = state.get("search_params", {})
    sort_by = p.get("sort_by", "BEST_MATCH")

    if sort_by == "LOWEST_PRICE":
        products.sort(key=lambda x: x.price)
    elif sort_by == "TOP_RATED":
        products.sort(key=lambda x: (x.rating, x.reviews), reverse=True)

    top_products = products[:3]

    summary_prompt = f"""
    User Request: "{state['user_input']}"
    
    Here are selected products:
    {[p.title for p in top_products]}

    Write a short helpful recommendation explaining why these are good options.
    Do NOT generate links or URLs.
    """

    try:
        res = client.models.generate_content(
            model="gemini-1.5-flash-latest",
            contents=summary_prompt
        )
        explanation = res.text.strip()
    except:
        explanation = "Here are the best available options."

    formatted_output = explanation + "\n\n"

    for p in top_products:
        formatted_output += (
            f"### {p.title}\n"
            f"Price: ₹{p.price}\n"
            f"Rating: {p.rating}★ ({p.reviews} reviews)\n"
            f"Store: {p.source}\n"
            f"![Image]({p.image_url})\n"
            f"[Buy Here]({p.link})\n\n"
        )

    return {"final_response": formatted_output}


# --- GRAPH BUILD ---
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

app = workflow.compile()

def main():
    print("--- 🛒 AMAZON & FLIPKART ONLY AGENT ---")
    while True:
        try:
            user_in = input("\nYou: ")
            if user_in.lower() in ["quit", "exit"]: break
            res = app.invoke({"user_input": user_in})
            print(f"\n🤖 {res['final_response']}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()