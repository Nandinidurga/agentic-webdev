from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    prompt: str
    plan: str
    api_spec: list[dict[str, Any]]
    context: str
    rag_chunks: list[dict[str, Any]]
    code: str
    backend_files: dict[str, str]
    frontend_files: dict[str, str]
    files: dict[str, str]
    execution_result: str
    backend_test_results: str
    errors: list[dict[str, Any]]
    iteration: int
    attempt: int
    cancel_event: Any
