from typing import TypedDict, List, Dict, Any

class AgentState(TypedDict):
    prompt: str
    plan: str
    context: str
    code: str
    files: Dict[str, str]
    execution_result: str
    errors: str
    iteration: int
