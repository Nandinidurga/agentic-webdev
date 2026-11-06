import os
import json
import sys
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from graph import create_graph

print("=== TESTING FULL-STACK AGENT WORKFLOW ===", flush=True)
graph = create_graph()

prompt = "Build a Task & Priority Tracker application with categories, due dates, and completion status"
initial_state = {"prompt": prompt, "iteration": 0}

print(f"\nInvoking LangGraph with prompt: '{prompt}'...", flush=True)
result = graph.invoke(initial_state)

print("\n--- 1. FULL-STACK ARCHITECTURAL PLAN ---")
print(result.get("plan", "")[:400] + "...\n[Plan Truncated for brevity]")

print("\n--- 2. STRUCTURED API SPECIFICATION ---")
api_spec = result.get("api_spec", [])
print(json.dumps(api_spec, indent=2))

print("\n--- 3. GENERATED FILES SUMMARY ---")
files = result.get("files", {})
backend_files = result.get("backend_files", {})
frontend_files = result.get("frontend_files", {})

print(f"Total Files: {len(files)}")
print(f"Backend Files ({len(backend_files)}): {list(backend_files.keys())}")
print(f"Frontend Files ({len(frontend_files)}): {list(frontend_files.keys())}")

print("\n--- 4. SAMPLE BACKEND SERVER SNIPPET (/server.js) ---")
server_code = files.get("/server.js") or files.get("server.js") or files.get("/server/server.js")
if server_code:
    print(server_code[:350] + "...\n[Server Code Truncated]")
else:
    print("WARNING: No server.js file found!")

print("\n--- 5. REVIEWER VALIDATION & EXECUTION RESULT ---")
print(result.get("execution_result", ""))

if not result.get("errors"):
    print("\n>>> SUCCESS: Full-Stack Generation & Validation Passed! <<<")
else:
    print(f"\n>>> WARNING: Reviewer reported errors: {result.get('errors')} <<<")
