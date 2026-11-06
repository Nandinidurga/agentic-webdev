import json
import re
from langchain_core.messages import SystemMessage, HumanMessage
from llm_factory import get_llm

def orchestrator_node(state):
    print("--- ORCHESTRATOR AGENT ---")
    prompt = state.get("prompt", "")
    
    llm = get_llm()
    
    system_prompt = """You are the Lead Architect & Orchestrator Agent for a Full-Stack AI Web Developer.
Your task is to analyze the user's prompt and formulate a comprehensive technical plan for building BOTH the Frontend and the Backend.

You must design:
1. BACKEND ARCHITECTURE (Node.js + Express.js):
   - Server entry point: `server.js` running on port 5000 with CORS and express.json().
   - In-memory / JSON store with realistic seed data matching the domain.
   - RESTful API endpoints covering full CRUD operations (e.g. GET /api/items, POST /api/items, PUT /api/items/:id, DELETE /api/items/:id, plus GET /api/health).
   - Input validation, clear error responses, and proper HTTP status codes.

2. FRONTEND ARCHITECTURE (React + Plain CSS):
   - Interactive UI components (main App.js, modular components, responsive layout).
   - Clean, modern Plain CSS styling in `/styles.css` using CSS variables, flexbox/grid layouts, cards, and animations (do NOT use Tailwind CSS or external CSS utility frameworks).
   - API client module (`services/api.js`) to consume backend endpoints with fallback data for preview.
   - State management, loading states, and optimistic or reactive UI updates.

3. STRUCTURED API CONTRACT:
   At the very end of your response, you MUST provide a JSON block with the exact list of API endpoints for the backend in this format:
   ```json:api_spec
   [
     {
       "method": "GET",
       "path": "/api/items",
       "description": "Retrieve all items",
       "sampleResponse": [{"id": 1, "name": "Sample"}]
     },
     {
       "method": "POST",
       "path": "/api/items",
       "description": "Create a new item",
       "sampleRequest": {"name": "New Item"},
       "sampleResponse": {"id": 2, "name": "New Item"}
     }
   ]
   ```

Output a clear, professional Markdown document containing the complete full-stack plan, followed by the ```json:api_spec block."""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"User Prompt: {prompt}")
    ]
    
    response = llm.invoke(messages)
    content = response.content
    if isinstance(content, list):
        content = "\n".join([c if isinstance(c, str) else c.get("text", str(c)) for c in content])
    content = str(content)
    
    # Extract api_spec
    api_spec = []
    
    # Match ```json:api_spec ... ``` or ```json ... ``` containing API specs
    match = re.search(r"```(?:json:api_spec|json)\s*\n(.*?)```", content, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(1).strip())
            if isinstance(parsed, list):
                api_spec = parsed
        except json.JSONDecodeError:
            pass
            
    # Fallback heuristic: search for any JSON array with 'method' and 'path'
    if not api_spec:
        array_match = re.search(r"\[\s*\{\s*\"method\".*?\}\s*\]", content, re.DOTALL)
        if array_match:
            try:
                parsed = json.loads(array_match.group(0))
                if isinstance(parsed, list):
                    api_spec = parsed
            except json.JSONDecodeError:
                pass
                
    print(f"Orchestrator planned {len(api_spec)} API endpoints.")
    
    return {
        "plan": content,
        "api_spec": api_spec
    }
