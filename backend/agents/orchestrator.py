from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
import os

def orchestrator_node(state):
    print("--- ORCHESTRATOR ---")
    prompt = state.get("prompt", "")
    
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash") # Switched to flash
    
    system_prompt = """You are the Orchestrator Agent for an AI Web Developer.
Your task is to analyze the user's prompt and break it down into a technical plan for building a web application.
Specify the frontend (e.g. Next.js, Tailwind), backend, and any key libraries needed.
Output a clear, step-by-step plan."""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=prompt)
    ]
    
    response = llm.invoke(messages)
    
    return {"plan": response.content, "iteration": state.get("iteration", 0) + 1}
