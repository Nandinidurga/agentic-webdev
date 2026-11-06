import os
from dotenv import load_dotenv, find_dotenv
from e2b_code_interpreter import Sandbox

load_dotenv(find_dotenv())

api_key = os.getenv("E2B_API_KEY")
print(f"E2B_API_KEY present: {bool(api_key)}")

try:
    with Sandbox.create() as sandbox:
        print("Sandbox started successfully.")
        execution = sandbox.run_code("print('Hello from E2B!')")
        print(f"Execution Output: {execution.text}")
except Exception as e:
    print(f"E2B Error: {e}")
