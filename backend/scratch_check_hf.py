import os
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

token = os.getenv('HF_TOKEN')
print(f"Loaded HF_TOKEN: {token[:5]}...{token[-5:]}" if token else "No HF_TOKEN found")

if token:
    try:
        res = requests.get('https://huggingface.co/api/whoami-v2', headers={'Authorization': f'Bearer {token}'})
        print(f"HF API Response Status: {res.status_code}")
        if res.status_code == 200:
            print("Token is valid! User:", res.json().get('name'))
        else:
            print("Response:", res.json())
    except Exception as e:
        print("Error connecting to HF API:", e)
