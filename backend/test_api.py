import requests
import json

user_prompt = input("Enter your prompt for the AI Web Developer: ")
if not user_prompt.strip():
    print("Prompt cannot be empty.")
    exit(1)

print("\nSending request to the backend. Please wait...")
response = requests.post("http://localhost:8000/generate", json={"prompt": user_prompt})
print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print("\n--- PLAN ---")
    print(data.get("plan", "No plan generated."))
    
    print("\n--- CODE ---")
    print(data.get("code", "No code generated."))
    
    print("\n--- EXECUTION RESULT ---")
    print(data.get("execution_result", "No execution result."))
else:
    print(response.json())
