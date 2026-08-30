import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
import re

def coder_node(state):
    print("--- CODER AGENT ---")
    plan = state.get("plan", "")
    context = state.get("context", "")
    errors = state.get("errors", "")
    
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash") # Switched to flash
    
    system_prompt = f"""You are the Coder Agent. Your job is to write the actual code for the web application based on the plan.
Context from RAG Knowledge Base: {context}

Output a strictly valid JSON object where the keys are the file paths and the values are the complete code content.
CRITICAL INSTRUCTIONS FOR SANDPACK COMPATIBILITY:
1. The main React component MUST be named '/App.js'. Do not use .jsx.
2. You can create other components like '/components/Counter.js'.
3. You can create CSS like '/styles.css' (and import it in App.js).
4. DO NOT generate 'index.html', 'main.jsx', 'vite.config.js' or any build tools.
5. If you need third-party libraries (e.g. 'react-router-dom', 'axios', 'framer-motion'), you MUST generate a '/package.json' file with a valid JSON object containing a "dependencies" key mapping package names to "*".
6. Assume 'react', 'react-dom', 'lucide-react', and 'tailwindcss' are already installed.

DO NOT output any markdown blocks like ```json. Output ONLY the raw JSON object."""

    prompt = f"Plan:\n{plan}\n\nPrevious Errors:\n{errors}\n\nGenerate the JSON file structure."
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=prompt)
    ]
    
    response = llm.invoke(messages)
    
    # Try to parse the JSON
    content = response.content.strip()
    # Robustly extract JSON block
    start_idx = content.find('{')
    end_idx = content.rfind('}')
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        content = content[start_idx:end_idx+1]
        
    try:
        files = json.loads(content)
        code = "JSON generated successfully."
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON: {e}")
        files = {}
        code = content
        
    return {"code": code, "files": files}
