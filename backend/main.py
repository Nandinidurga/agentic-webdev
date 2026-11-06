"""
Agentic Full-Stack Web Development Studio - Core FastAPI Backend

Coordinates the multi-agent cognitive loop powered by LangGraph:
- Orchestrator: System architecture & API specification planning
- Knowledge Dual RAG: Context retrieval for backend and frontend libraries
- Coder: High-fidelity parallel generation of Node.js/Express and React code
- Reviewer: Deterministic AST & static validator suite with structured errors

Security & Production Hardening:
- slowapi rate limiting (configurable via RATE_LIMIT env var, default: 10/minute)
- Async generation execution timeout (configurable via GENERATION_TIMEOUT env var, default: 180s per attempt)
- Shared cancellation flag (threading.Event) ensuring 504 timeouts actually abort worker threads
- Sanitized 500/504 error reporting (hiding internal exception stack traces, returning unique request_ids)
- Safe CORS configuration parsed from FRONTEND_ORIGINS (no wildcard credentials)
- Strict prompt validation via Pydantic field validators
"""

import os
import time
import uuid
import logging
import asyncio
import threading
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Load environment configuration
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("agentic-studio")

START_TIME = time.time()
MAX_PROMPT_LENGTH = int(os.getenv("MAX_PROMPT_LENGTH", "4000"))
GENERATION_TIMEOUT_SECONDS = int(os.getenv("GENERATION_TIMEOUT", "180"))

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Agentic Full-Stack Studio Backend",
    version="2.1.0",
    description="Multi-Agent Full-Stack Software Engineering Engine"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS using FRONTEND_ORIGINS env variable
# Eliminates wildcard + credentials vulnerability
raw_origins = os.getenv("FRONTEND_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001")
allowed_origins = [orig.strip() for orig in raw_origins.split(",") if orig.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Lazy import graph to allow graceful fallback when LLM keys are absent
_graph = None

def get_graph():
    global _graph
    if _graph is None:
        try:
            from graph import create_graph
            _graph = create_graph()
        except Exception as e:
            logger.error(f"Failed to initialize multi-agent LangGraph workflow: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Graph initialization failed: {e}"
            )
    return _graph

class PromptRequest(BaseModel):
    prompt: str = Field(..., description="Application specification prompt", min_length=1)

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Prompt cannot be empty or whitespace only.")
        if len(clean) > MAX_PROMPT_LENGTH:
            raise ValueError(
                f"Prompt length exceeds maximum allowed length of {MAX_PROMPT_LENGTH} characters "
                f"(received {len(clean)} characters)."
            )
        return clean

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "Agentic Full-Stack Studio Backend",
        "version": "2.1.0",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    groq_configured = bool(os.getenv("GROQ_API_KEY"))
    gemini_configured = bool(os.getenv("GEMINI_API_KEY"))
    chroma_exists = os.path.exists("./chroma_db")
    
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
    (Orchestrator -> Knowledge Dual RAG -> Coder -> Reviewer Static Validators).
    Includes slowapi rate limiting, per-attempt generation timeout, and sanitized error responses.
    """
    cancel_event = threading.Event()
    max_attempts = int(os.getenv("MAX_ATTEMPTS", "3"))
    attempt_timeout = float(GENERATION_TIMEOUT_SECONDS)
    total_timeout = attempt_timeout * max_attempts + 30.0

    try:
        graph = get_graph()
        initial_state = {
            "prompt": body.prompt,
            "attempt": 0,
            "cancel_event": cancel_event
        }
        
        # Run graph in worker thread with timeout enforcement
        result = await asyncio.wait_for(
            asyncio.to_thread(graph.invoke, initial_state),
            timeout=total_timeout
        )
        
        raw_errors = result.get("errors")
        errors_list: List[Any] = []
        if isinstance(raw_errors, list):
            errors_list = raw_errors
        elif isinstance(raw_errors, str) and raw_errors.strip():
            errors_list = [{"file": "general", "line": 1, "rule": "general", "message": raw_errors.strip()}]
            
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
    except (asyncio.TimeoutError, TimeoutError) as te:
        cancel_event.set()
        req_id = str(uuid.uuid4())
        logger.error(f"[Request ID {req_id}] Generation timed out: {te}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={
                "message": f"Generation timed out after {int(attempt_timeout)} seconds per-attempt budget. Please try a more specific prompt or retry.",
                "request_id": req_id
            }
        )
    except ValueError as ve:
        cancel_event.set()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except HTTPException:
        cancel_event.set()
        raise
    except Exception as e:
        cancel_event.set()
        req_id = str(uuid.uuid4())
        logger.error(f"[Request ID {req_id}] Unhandled error during application generation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "An internal server error occurred while processing your generation request.",
                "request_id": req_id
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
