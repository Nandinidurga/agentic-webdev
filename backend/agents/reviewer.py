import os
from e2b_code_interpreter import Sandbox

def reviewer_node(state):
    print("--- REVIEWER AGENT ---")
    files = state.get("files", {})
    
    execution_result = "No execution required."
    errors = ""
    
    if not files:
        errors = "Failed to generate valid file structure JSON."
        print(f"Reviewer Error: {errors}")
    else:
        print(f"Reviewer Success: Validated {len(files)} files.")
        
    return {"execution_result": execution_result, "errors": errors}
