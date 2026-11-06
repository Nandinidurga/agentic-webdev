
from dotenv import find_dotenv, load_dotenv
from google import genai

load_dotenv(find_dotenv())

client = genai.Client()
for model in client.models.list():
    print(model.name)
