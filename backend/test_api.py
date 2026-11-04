import sys
import json
import requests

def test_backend_generation():
    # Allow prompt via CLI arg or interactive prompt
    if len(sys.argv) > 1:
        user_prompt = " ".join(sys.argv[1:]).strip()
    else:
        user_prompt = input("Enter your prompt for the AI Web Developer: ").strip()

    if not user_prompt:
        user_prompt = "Task & Priority Tracker with categories, due dates, and completion status"
        print(f"Using default sample prompt: '{user_prompt}'")

    api_url = "http://localhost:8000"

    # 1. Health check check
    try:
        health_res = requests.get(f"{api_url}/health", timeout=3)
        if health_res.status_code == 200:
            health_data = health_res.json()
            print(f"[OK] Backend health: {health_data.get('status')} (Uptime: {health_data.get('uptime')}s)")
        else:
            print(f"[WARN] Backend health returned status {health_res.status_code}")
    except requests.exceptions.RequestException:
        print("[ERROR] Could not reach backend at http://localhost:8000.")
        print("Please start the server first: uvicorn main:app --reload --port 8000")
        sys.exit(1)

    print(f"\nSending generation request for: '{user_prompt}'...")
    try:
        response = requests.post(
            f"{api_url}/generate",
            json={"prompt": user_prompt},
            timeout=120
        )
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("\n=== 1. ARCHITECTURAL BLUEPRINT ===")
            print(data.get("plan", "No plan generated.")[:350] + "...\n[Plan Truncated]")

            api_spec = data.get("api_spec", [])
            print(f"\n=== 2. CONFIGURED API SPECIFICATION ({len(api_spec)} endpoints) ===")
            for ep in api_spec:
                print(f"• {ep.get('method', 'GET')} {ep.get('path')} - {ep.get('description')}")

            backend_files = data.get("backend_files", {})
            frontend_files = data.get("frontend_files", {})
            print(f"\n=== 3. GENERATED FULL-STACK FILES ===")
            print(f"• Backend ({len(backend_files)}): {list(backend_files.keys())}")
            print(f"• Frontend ({len(frontend_files)}): {list(frontend_files.keys())}")

            print("\n=== 4. REVIEWER VALIDATION LOGS ===")
            print(data.get("execution_result", "No execution result."))
            print("\n>>> Verification Completed Successfully! <<<")
        else:
            print("[ERROR] Request failed with response:")
            print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_backend_generation()
