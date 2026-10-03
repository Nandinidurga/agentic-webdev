import os
import time
from typing import Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv())

# Map HF_TOKEN to HUGGINGFACEHUB_API_TOKEN for Langchain compatibility
if "HF_TOKEN" in os.environ and "HUGGINGFACEHUB_API_TOKEN" not in os.environ:
    os.environ["HUGGINGFACEHUB_API_TOKEN"] = os.environ["HF_TOKEN"]

START_TIME = time.time()

app = FastAPI(
    title="Agentic Full-Stack Studio API",
    description="Multi-agent LangGraph engine generating React frontends and Express.js REST backends",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PromptRequest(BaseModel):
    prompt: str = Field(
        ..., 
        description="Natural language description of the web application to engineer",
        min_length=3,
        max_length=5000
    )

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Prompt cannot be empty or contain only whitespace.")
        if len(cleaned) < 3:
            raise ValueError("Prompt must be at least 3 characters long.")
        return cleaned

# Cached workflow graph
_compiled_graph = None

def get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        from graph import create_graph
        _compiled_graph = create_graph()
    return _compiled_graph

@app.get("/")
def root():
    """Root metadata endpoint."""
    return {
        "service": "Agentic Full-Stack Studio API",
        "version": "2.0.0",
        "status": "operational",
        "endpoints": {
            "generate": "POST /generate",
            "health": "GET /health"
        }
    }

@app.get("/health")
def health_check():
    """Service health inspection endpoint."""
    groq_configured = bool(os.getenv("GROQ_API_KEY", "").strip() and os.getenv("GROQ_API_KEY") != "gsk_your_groq_api_key_here")
    gemini_configured = bool(os.getenv("GOOGLE_API_KEY", "").strip() and os.getenv("GOOGLE_API_KEY") != "your_gemini_api_key_here")
    chroma_exists = os.path.exists(os.path.abspath(os.path.join(os.path.dirname(__file__), "chroma_db")))

    return {
        "status": "healthy",
        "uptime": round(time.time() - START_TIME, 2),
        "llm_providers": {
            "groq_configured": groq_configured,
            "gemini_configured": gemini_configured,
            "active_model": os.getenv("GROQ_MODEL", "openai/gpt-oss-20b") if groq_configured else os.getenv("LLM_MODEL", "gemini-1.5-flash")
        },
        "rag_vector_store": {
            "chroma_db_present": chroma_exists
        }
    }

@app.post("/generate")
def generate_app(request: PromptRequest):
    """
    Main agentic entry point: runs the LangGraph cognitive loop
    (Orchestrator -> Knowledge Dual RAG -> Coder -> Reviewer Auto-Healer).
    """
    try:
        graph = get_graph()
        initial_state = {"prompt": request.prompt, "iteration": 0}
        
        # Run graph
        result = graph.invoke(initial_state)
        
        return {
            "status": "success", 
            "message": "Workflow completed",
            "plan": result.get("plan"),
            "code": result.get("code"),
            "files": result.get("files", {}),
            "backend_files": result.get("backend_files", {}),
            "frontend_files": result.get("frontend_files", {}),
            "api_spec": result.get("api_spec", []),
            "execution_result": result.get("execution_result"),
            "backend_test_results": result.get("backend_test_results"),
            "errors": result.get("errors")
        }
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Generation failed: {str(e)}"
        )
