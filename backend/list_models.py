from google import genai
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

client = genai.Client()
for model in client.models.list():
    print(model.name)
