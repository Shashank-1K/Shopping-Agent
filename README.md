

# 🛒 Shopping Agent

An AI-powered e-commerce shopping assistant built with **LangGraph** and **Google Gemini**. This agent understands natural language queries, searches across **Amazon** and **Flipkart** (India) in real-time, filters products by price and reviews, and provides intelligent recommendations — available as both a **CLI tool** and a **FastAPI REST API**.

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/AI-LangGraph-orange)
![Gemini](https://img.shields.io/badge/LLM-Google%20Gemini-4285F4?logo=google&logoColor=white)
![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📌 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
- [Configuration](#configuration)
- [Usage](#usage)
  - [CLI Mode](#cli-mode)
  - [API Mode](#api-mode)
- [API Documentation](#api-documentation)
- [Examples](#examples)
- [Tech Stack](#tech-stack)
- [Troubleshooting](#troubleshooting)

---

## Overview

**Shopping Agent** is a conversational AI agent that takes natural language shopping requests (e.g., _"Find me a popular gaming mouse under ₹2000"_), intelligently parses the intent using Google Gemini, searches across Amazon and Flipkart via the RapidAPI Real-Time Product Search API, filters and ranks results, and returns curated recommendations with explanations.

The agent is available in two modes:

| Mode | File | Description |
|------|------|-------------|
| **CLI** | `graph_agent.py` | Interactive command-line interface for direct conversation |
| **API** | `api.py` | RESTful FastAPI server for integration with frontends and other services |

---

## Features

- 🧠 **Natural Language Understanding** — Powered by Google Gemini to extract query, price range, sorting preference, and review thresholds from free-text input.
- 🔍 **Real-Time Multi-Store Search** — Fetches live product data from **Amazon India** and **Flipkart** simultaneously using the RapidAPI Real-Time Product Search API.
- 💰 **Smart Filtering** — Supports filtering by minimum/maximum price, minimum review count, and sorting by best match, lowest price, or top-rated.
- 📊 **Intelligent Ranking** — Sorts results by price or rating based on user intent before presenting top recommendations.
- 💬 **AI-Generated Recommendations** — Uses Gemini to generate human-friendly explanations of why selected products are good choices.
- 🌐 **REST API** — Full FastAPI server with CORS support for frontend integration.
- 🏗️ **Clean Architecture** — Follows hexagonal (ports & adapters) architecture for easy extensibility to new e-commerce platforms.
- 🔄 **Agentic Workflow** — Uses LangGraph's `StateGraph` for a structured, node-based agent pipeline with conditional routing.

---

## Architecture

The project follows the **Hexagonal Architecture (Ports & Adapters)** pattern:

```
┌─────────────────────────────────────────────────────────────┐
│                      LangGraph Agent                        │
│                                                             │
│   ┌─────────────┐      ┌────────────┐     ┌───────────────┐ │
│   │ Understand  │────▶│   Search   │────▶│    Respond    │ │
│   │  (Gemini)   │      │   (API)    │     │   (Gemini)    │ │
│   └─────────────┘      └────────────┘     └───────────────┘ │
│         │                                                   │
│         │ (no query found)                                  │
│         └────────────────────────────▶ Respond ────▶ END   │
└─────────────────────────────────────────────────────────────┘

┌────────────────────┐         ┌──────────────────────────────┐
│    Core Layer      │         │      Adapters Layer          │
│                    │         │                              │
│  ports.py          │◀────────│  universal_adapter.py       │
│  (Product,         │         │  (RapidAPI integration)      │
│  EcommerceProvider)│         │                              │
└────────────────────┘         └──────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    Entry Points                             │
│                                                             │
│   graph_agent.py  ──▶  CLI (Interactive Terminal)           │
│   api.py          ──▶  FastAPI REST Server (HTTP)           │
└─────────────────────────────────────────────────────────────┘
```

### Agent Flow

```
User Input
    │
    ▼
┌──────────────┐
│  UNDERSTAND  │  ← Gemini parses intent into structured params
└──────┬───────┘
       │
       ▼
   Has query? ──No──▶ RESPOND (fallback message) ──▶ END
       │
      Yes
       │
       ▼
┌──────────────┐
│    SEARCH    │  ← RapidAPI fetches products from Amazon & Flipkart
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   RESPOND    │  ← Gemini generates recommendation + formatted output
└──────┬───────┘
       │
       ▼
      END
```

---

## Project Structure

```
Shopping_Agent/
│
├── .gitignore                  # Git ignore rules
├── graph_agent.py              # CLI entry point — LangGraph workflow & interactive loop
├── api.py                      # FastAPI entry point — REST API server
├── README.md                   # Project documentation (this file)
├── requirements.txt            # Python dependencies
│
├── adapters/                   # Adapters layer (external integrations)
│   ├── __init__.py
│   └── universal_adapter.py    # RapidAPI Real-Time Product Search adapter
│
└── core/                       # Core domain layer (interfaces & models)
    ├── __init__.py
    └── ports.py                # Product dataclass & EcommerceProvider abstract class
```

### File Descriptions

| File | Description |
|------|-------------|
| `graph_agent.py` | **CLI entry point.** Defines the LangGraph `StateGraph` with three nodes (`understand`, `search`, `respond`), conditional routing, and an interactive terminal loop. |
| `api.py` | **API entry point.** Wraps the same LangGraph agent workflow in a FastAPI server with a `/chat` POST endpoint. Includes CORS middleware for frontend integration. |
| `core/ports.py` | **Core domain layer.** Contains the `Product` dataclass (title, price, rating, reviews, etc.) and the `EcommerceProvider` abstract base class defining the search interface contract. |
| `adapters/universal_adapter.py` | **Adapter implementation.** `UniversalSearchAdapter` implements `EcommerceProvider` using the RapidAPI Real-Time Product Search API, targeting Amazon India and Flipkart. Handles price parsing, review extraction, image URLs, and result filtering. |
| `requirements.txt` | Python package dependencies. |
| `.gitignore` | Specifies files and folders excluded from version control. |

---

## How It Works

### 1. Understand Node (`node_understand`)

- Takes the user's natural language input.
- Sends it to **Google Gemini** with a structured extraction prompt.
- Extracts structured parameters: `query`, `max_price`, `min_price`, `min_reviews`, `sort_by`.
- Falls back to using raw input as the query if LLM parsing fails.

### 2. Search Node (`node_search`)

- Uses `UniversalSearchAdapter` to call the **RapidAPI Real-Time Product Search v2** endpoint.
- Searches specifically on **Amazon** and **Flipkart** (`stores: "amazon,flipkart"`), targeting India (`country: "in"`).
- Fetches up to 30 results per query.
- Parses and normalizes product data (title, price, rating, reviews, images, links) into standardized `Product` objects.
- Applies server-side and client-side filtering (price range, minimum reviews).

### 3. Respond Node (`node_respond`)

- Sorts results by price or rating based on the extracted `sort_by` parameter.
- Selects the **top 3 products**.
- Sends product titles to **Gemini** to generate a helpful recommendation summary explaining why these are good choices.
- Formats the final output with Markdown including product details, ratings, store info, images, and buy links.

### 4. Conditional Routing

- If the `understand` node fails to extract a valid query, the agent skips the search step and directly responds with a fallback message — no unnecessary API calls.

---

## Prerequisites

Before running the agent, ensure you have:

| Requirement | Details |
|-------------|---------|
| **Python** | Version 3.9 or higher |
| **Google Gemini API Key** | Get it from [Google AI Studio](https://aistudio.google.com/app/apikey) |
| **RapidAPI Key** | Subscribe to [Real-Time Product Search](https://rapidapi.com/letscrape-6bRBa3QguO5/api/real-time-product-search) on RapidAPI |

---

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/Shopping_Agent.git
cd Shopping_Agent
```

### 2. Create and Activate a Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Additionally, install the Google Gemini client and FastAPI dependencies (if not already in requirements):

```bash
pip install google-genai fastapi uvicorn
```

---

## Configuration

### Create a `.env` File

Create a `.env` file in the project root directory:

```env
RAPIDAPI_KEY=your_rapidapi_key_here
GEMINI_API_KEY=your_google_gemini_api_key_here
```

### Getting Your API Keys

| Key | Source | Purpose |
|-----|--------|---------|
| `RAPIDAPI_KEY` | [RapidAPI](https://rapidapi.com/) → Subscribe to [Real-Time Product Search](https://rapidapi.com/letscrape-6bRBa3QguO5/api/real-time-product-search) | Fetching live product data from Amazon & Flipkart |
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/app/apikey) | Natural language understanding & recommendation generation |

> ⚠️ **Never commit your `.env` file to version control.** It is already included in `.gitignore`.

---

## Usage

### CLI Mode

Run the interactive command-line agent:

```bash
python graph_agent.py
```

**Example Session:**

```
--- 🛒 AMAZON & FLIPKART ONLY AGENT ---

You: I need a durable running shoe under 5000 rupees suitable for marathon

■ [Understand] Parsing: I need a durable running shoe under 5000 rupees...
 -> Extracted: {'query': 'running shoe', 'max_price': 5000, 'min_reviews': 0, 'sort_by': 'BEST_MATCH'}
[API] Searching: 'running shoe' on Amazon/Flipkart...

🛒 Based on your request, here are the top choices:

### Nike Downshifter 12
Price: ₹3499
Rating: 4.2★ (1200 reviews)
Store: Amazon
[Buy Here](https://...)

### Adidas RunFalcon 3.0
Price: ₹2999
Rating: 4.4★ (890 reviews)
Store: Flipkart
[Buy Here](https://...)

You: quit
```

Type `quit` or `exit` to stop the agent.

---

### API Mode

Start the FastAPI server:

```bash
python api.py
```

Or using uvicorn directly:

```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

The server will start at `http://localhost:8000`.

**Interactive API Docs:** Open `http://localhost:8000/docs` in your browser for the auto-generated Swagger UI.

---

## API Documentation

### `POST /chat`

Send a natural language shopping query and receive product recommendations.

**Request:**

```json
{
  "query": "best wireless earbuds under 3000 with good reviews"
}
```

**Response:**

```json
{
  "response": "Here are some excellent wireless earbuds under ₹3000...\n\n### boAt Airdopes 141\n**Price:** ₹1299\n**Rating:** 4.1★ (45230 reviews)\n**Store:** Amazon\n[Buy Now](https://...)\n\n...",
  "products": [
    {
      "title": "boAt Airdopes 141",
      "price": 1299.0,
      "link": "https://...",
      "image": "https://...",
      "rating": 4.1,
      "reviews": 45230
    },
    {
      "title": "Realme Buds T300",
      "price": 1799.0,
      "link": "https://...",
      "image": "https://...",
      "rating": 4.3,
      "reviews": 12400
    },
    {
      "title": "OnePlus Nord Buds 2r",
      "price": 2299.0,
      "link": "https://...",
      "image": "https://...",
      "rating": 4.2,
      "reviews": 8900
    }
  ]
}
```

**cURL Example:**

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "gaming mouse under 2000"}'
```

**Python Example:**

```python
import requests

response = requests.post(
    "http://localhost:8000/chat",
    json={"query": "gaming mouse under 2000"}
)
data = response.json()
print(data["response"])
```

**JavaScript / Fetch Example:**

```javascript
const response = await fetch("http://localhost:8000/chat", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ query: "wireless earbuds under 3000" })
});
const data = await response.json();
console.log(data.response);
```

### API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/chat` | Send a shopping query and receive AI-curated product recommendations |
| `GET` | `/docs` | Swagger UI — Interactive API documentation |
| `GET` | `/redoc` | ReDoc — Alternative API documentation |

---

## Examples

### Natural Language Query Examples

| User Input | Extracted Parameters |
|------------|---------------------|
| `"gaming mouse under 2000"` | `query: "gaming mouse"`, `max_price: 2000` |
| `"popular wireless earbuds between 1000 and 3000"` | `query: "wireless earbuds"`, `min_price: 1000`, `max_price: 3000`, `min_reviews: 100`, `sort_by: "TOP_RATED"` |
| `"cheapest mechanical keyboard"` | `query: "mechanical keyboard"`, `sort_by: "LOWEST_PRICE"` |
| `"top rated laptop stand"` | `query: "laptop stand"`, `sort_by: "TOP_RATED"` |
| `"iPhone 15 case with good reviews"` | `query: "iPhone 15 case"`, `min_reviews: 50` |
| `"best headphones for gym under 5000"` | `query: "headphones for gym"`, `max_price: 5000`, `sort_by: "TOP_RATED"` |

---

## Tech Stack

| Technology | Purpose |
|------------|---------|
| [Python 3.9+](https://www.python.org/) | Core programming language |
| [LangGraph](https://github.com/langchain-ai/langgraph) | Agentic workflow orchestration (StateGraph) |
| [Google Gemini](https://ai.google.dev/) | LLM for natural language understanding & recommendation generation |
| [FastAPI](https://fastapi.tiangolo.com/) | REST API framework for the HTTP server |
| [Uvicorn](https://www.uvicorn.org/) | ASGI server for running FastAPI |
| [RapidAPI](https://rapidapi.com/) | Real-Time Product Search API (Amazon & Flipkart) |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | Environment variable management |
| [Requests](https://requests.readthedocs.io/) | HTTP client for external API calls |
| [Pydantic](https://docs.pydantic.dev/) | Data validation for API request/response models |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'google.genai'` | Run `pip install google-genai` |
| `ModuleNotFoundError: No module named 'fastapi'` | Run `pip install fastapi uvicorn` |
| `Missing API Keys in .env file` | Ensure `.env` file exists in the project root with both `RAPIDAPI_KEY` and `GEMINI_API_KEY` |
| `API returned 403` | Verify your `RAPIDAPI_KEY` is valid and you are subscribed to the Real-Time Product Search API |
| `API returned 429` | You have hit the RapidAPI rate limit. Wait a moment or upgrade your plan |
| `Invalid JSON from API` | The API may be temporarily unavailable. Retry after a few seconds |
| `No products found` | Try broadening your search query or removing strict price/review filters |
| `Gemini parsing fails` | The agent gracefully falls back to using raw input as the query. Verify your `GEMINI_API_KEY` is valid |
| `.env not loading` | Ensure `.env` is in the project root and `python-dotenv` is installed (`pip install python-dotenv`) |
| `CORS errors from frontend` | The API server has CORS enabled for all origins by default. For production, restrict `allow_origins` in `api.py` |
| `Port 8000 already in use` | Change the port: `uvicorn api:app --port 8001` |

---


```
