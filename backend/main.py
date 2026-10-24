import os
import time
import uuid
import asyncio
import logging
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv, find_dotenv

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("agentic_ide_backend")

# Load environment variables
load_dotenv(find_dotenv())

# Map HF_TOKEN to HUGGINGFACEHUB_API_TOKEN for Langchain compatibility
if "HF_TOKEN" in os.environ and "HUGGINGFACEHUB_API_TOKEN" not in os.environ:
    os.environ["HUGGINGFACEHUB_API_TOKEN"] = os.environ["HF_TOKEN"]

START_TIME = time.time()
GENERATION_TIMEOUT_SECONDS = int(os.getenv("GENERATION_TIMEOUT", "120"))
MAX_PROMPT_LENGTH = int(os.getenv("MAX_PROMPT_LENGTH", "5000"))

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

app = FastAPI(
    title="Agentic Full-Stack Studio API",
    description="Multi-agent LangGraph engine generating React frontends and Express.js REST backends",
    version="2.1.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS origins from environment variable (removes wildcard + credentials combination)
raw_origins = os.getenv("FRONTEND_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
allowed_origins = [orig.strip() for orig in raw_origins.split(",") if orig.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PromptRequest(BaseModel):
    prompt: str = Field(
        ..., 
        description="Natural language description of the web application to engineer",
        min_length=3,
        max_length=MAX_PROMPT_LENGTH
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
        "version": "2.1.0",
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
        },
        "config": {
            "max_attempts": int(os.getenv("MAX_ATTEMPTS", "3")),
            "generation_timeout": GENERATION_TIMEOUT_SECONDS,
            "heal_regex_enabled": os.getenv("HEAL_REGEX", "0").strip().lower() in ("1", "true")
        }
    }

@app.post("/generate")
@limiter.limit(os.getenv("RATE_LIMIT", "10/minute"))
async def generate_app(request: Request, body: PromptRequest):
    """
    Main agentic entry point: runs the LangGraph cognitive loop
    (Orchestrator -> Knowledge Dual RAG -> Coder -> Reviewer Auto-Healer).
    Includes slowapi rate limiting, 120s execution timeout, and sanitized error responses.
    """
    try:
        graph = get_graph()
        initial_state = {"prompt": body.prompt, "attempt": 0}
        
        # Run graph in worker thread with timeout enforcement
        result = await asyncio.wait_for(
            asyncio.to_thread(graph.invoke, initial_state),
            timeout=float(GENERATION_TIMEOUT_SECONDS)
        )
        
        raw_errors = result.get("errors")
        errors_list: List[str] = []
        if isinstance(raw_errors, list):
            errors_list = [str(e) for e in raw_errors if e]
        elif isinstance(raw_errors, str) and raw_errors.strip():
            errors_list = [raw_errors.strip()]
            
        has_remaining_errors = bool(errors_list)
        
        return {
            "status": "partial" if has_remaining_errors else "success",
            "message": "Workflow completed with non-fatal issues" if has_remaining_errors else "Workflow completed",
            "plan": result.get("plan"),
            "code": result.get("code"),
            "files": result.get("files", {}),
            "backend_files": result.get("backend_files", {}),
            "frontend_files": result.get("frontend_files", {}),
            "api_spec": result.get("api_spec", []),
            "execution_result": result.get("execution_result"),
            "backend_test_results": result.get("backend_test_results"),
            "errors": errors_list,
            "attempt": result.get("attempt", 1)
        }
    except asyncio.TimeoutError:
        req_id = str(uuid.uuid4())
        logger.error(f"[Request ID {req_id}] Generation timed out after {GENERATION_TIMEOUT_SECONDS}s for prompt: {body.prompt[:80]}...")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={
                "message": f"Generation timed out after {GENERATION_TIMEOUT_SECONDS} seconds. Please try a more specific prompt or retry.",
                "request_id": req_id
            }
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        req_id = str(uuid.uuid4())
        logger.error(f"[Request ID {req_id}] Unhandled error during application generation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "An internal server error occurred while processing your generation request.",
                "request_id": req_id
            }
        )
