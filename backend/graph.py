import os
from langgraph.graph import StateGraph, END
from state import AgentState
from agents.orchestrator import orchestrator_node
from agents.knowledge import knowledge_node
from agents.coder import coder_node
from agents.reviewer import reviewer_node

def should_continue(state):
    errors = state.get("errors")
    attempt = state.get("attempt", 0)
    max_attempts = int(os.getenv("MAX_ATTEMPTS", "3"))
    
    if errors and attempt < max_attempts:
        print(f"Errors found, returning to coder (attempt {attempt}/{max_attempts})...")
        return "coder"
    return END

def create_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("knowledge", knowledge_node)
    workflow.add_node("coder", coder_node)
    workflow.add_node("reviewer", reviewer_node)
    
    workflow.set_entry_point("orchestrator")
    
    workflow.add_edge("orchestrator", "knowledge")
    workflow.add_edge("knowledge", "coder")
    workflow.add_edge("coder", "reviewer")
    
    workflow.add_conditional_edges(
        "reviewer",
        should_continue,
        {
            "coder": "coder",
            END: END
        }
    )
    
    return workflow.compile()
