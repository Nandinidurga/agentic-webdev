from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
import os
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv())

# Map HF_TOKEN to HUGGINGFACEHUB_API_TOKEN for Langchain compatibility
if "HF_TOKEN" in os.environ and "HUGGINGFACEHUB_API_TOKEN" not in os.environ:
    os.environ["HUGGINGFACEHUB_API_TOKEN"] = os.environ["HF_TOKEN"]

app = FastAPI(title="Agentic Web Dev API")

# Allow CORS so the frontend on port 3000 can talk to the backend on port 8000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PromptRequest(BaseModel):
    prompt: str = Field(
        min_length=1,
        max_length=5000,
        description="A non-empty prompt describing the web application to generate."
    )

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, value):
        if not value.strip():
            raise ValueError(
                "Prompt cannot be empty or contain only whitespace."
            )
        return value

@app.post("/generate")
def generate_app(request: PromptRequest):
    try:
        from graph import create_graph
        graph = create_graph()
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
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
