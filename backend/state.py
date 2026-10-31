from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict, total=False):
    prompt: str
    plan: str
    api_spec: List[Dict[str, Any]]
    context: str
    rag_chunks: List[Dict[str, Any]]
    code: str
    backend_files: Dict[str, str]
    frontend_files: Dict[str, str]
    files: Dict[str, str]
    execution_result: str
    backend_test_results: str
    errors: List[Dict[str, Any]]
    iteration: int
    attempt: int
