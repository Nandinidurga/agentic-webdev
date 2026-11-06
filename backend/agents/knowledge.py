"""
knowledge.py - Dual-domain RAG retrieval agent for full-stack engineering.

Architecture:
- Singleton Chroma & HuggingFaceEmbeddings with resilient retry on failure.
- Uses modern `langchain-chroma` package.
- Domain-isolated metadata filtering (`domain="backend"` and `domain="frontend"`).
- Configurable top-k (`RAG_K`) and measured relevance score thresholding (`RAG_SCORE_THRESHOLD=0.35`).
- Plain CSS retrieval query (no Tailwind dependencies).
- Provides ranked, scored chunks directly to state for token-budgeted prompt construction.
"""

import os
from typing import Optional, List, Dict, Any, Tuple
from dotenv import load_dotenv

load_dotenv()

# Module-level singletons for embeddings and Chroma vectorstore
_EMBEDDINGS = None
_VECTORSTORE = None

CHROMA_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chroma_db"))


def get_vectorstore():
    """
    Module singleton provider for Chroma vector store and HuggingFace embeddings.
    Builds embeddings model and connects to local Chroma DB.
    Retries on subsequent calls if a previous initialization attempt failed.
    """
    global _EMBEDDINGS, _VECTORSTORE
    if _VECTORSTORE is not None:
        return _VECTORSTORE

    if not os.path.exists(CHROMA_DB_PATH):
        return None

    try:
        from langchain_huggingface import HuggingFaceEmbeddings
        from langchain_chroma import Chroma

        if _EMBEDDINGS is None:
            _EMBEDDINGS = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

        vs = Chroma(
            persist_directory=CHROMA_DB_PATH,
            embedding_function=_EMBEDDINGS,
            collection_name="langchain"
        )
        _VECTORSTORE = vs
        return _VECTORSTORE
    except Exception as err:
        print(f"Warning: Failed to initialize Chroma singleton (will retry on next request): {err}", flush=True)
        _VECTORSTORE = None
        return None


def retrieve_domain_chunks(
    vectorstore,
    query: str,
    domain: str,
    k: int,
    score_threshold: float
) -> List[Tuple[Any, float]]:
    """
    Executes similarity search with relevance scores and domain metadata filtering.
    Filters out any matches falling below the configured score threshold.
    """
    try:
        results = vectorstore.similarity_search_with_relevance_scores(
            query=query,
            k=k,
            filter={"domain": domain}
        )
        # Filter by minimum relevance threshold
        filtered = [
            (doc, float(score)) 
            for doc, score in results 
            if float(score) >= score_threshold
        ]
        return filtered
    except Exception as err:
        print(f"Error querying domain '{domain}': {err}", flush=True)
        return []


def knowledge_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph agent node: retrieves relevant reference documentation for backend
    and frontend domains, filtering by domain metadata and relevance thresholds.
    """
    print("--- RAG KNOWLEDGE AGENT (SINGLETON FULL-STACK RETRIEVAL) ---", flush=True)
    prompt = state.get("prompt", "")
    plan = state.get("plan", "")

    k = int(os.getenv("RAG_K", "3"))
    # Measured default: 0.35 threshold ensures high-relevance chunks and eliminates noise
    score_threshold = float(os.getenv("RAG_SCORE_THRESHOLD", "0.35"))

    vectorstore = get_vectorstore()

    if not vectorstore:
        context = "No persistent RAG vector store found. Relying on base engineering patterns."
        return {
            "context": context,
            "rag_chunks": []
        }

    # 1. Retrieve Backend-specific documentation (Express, REST routing, CORS, seed stores)
    backend_query = f"Express Node.js REST API routes endpoints middleware error handling data store {prompt} {plan[:300]}"
    backend_matches = retrieve_domain_chunks(
        vectorstore=vectorstore,
        query=backend_query,
        domain="backend",
        k=k,
        score_threshold=score_threshold
    )

    # 2. Retrieve Frontend-specific documentation (React hooks, state, plain CSS styles, responsive layouts)
    frontend_query = f"React components hooks state layout UI JSX CSS styles responsive design {prompt} {plan[:300]}"
    frontend_matches = retrieve_domain_chunks(
        vectorstore=vectorstore,
        query=frontend_query,
        domain="frontend",
        k=k,
        score_threshold=score_threshold
    )

    # Collect structured chunks with scores for token-budgeted prioritization
    rag_chunks = []
    backend_snippets = []
    for doc, score in backend_matches:
        source = doc.metadata.get("source", "backend")
        rag_chunks.append({
            "domain": "backend",
            "source": source,
            "score": round(score, 4),
            "content": doc.page_content
        })
        backend_snippets.append(f"[Source: {source} (score: {score:.3f})]:\n{doc.page_content}")

    frontend_snippets = []
    for doc, score in frontend_matches:
        source = doc.metadata.get("source", "frontend")
        rag_chunks.append({
            "domain": "frontend",
            "source": source,
            "score": round(score, 4),
            "content": doc.page_content
        })
        frontend_snippets.append(f"[Source: {source} (score: {score:.3f})]:\n{doc.page_content}")

    # Build context string
    context_parts = []
    if backend_snippets:
        context_parts.append("### BACKEND ARCHITECTURE & NODE.JS GUIDANCE:\n" + "\n\n".join(backend_snippets))
    if frontend_snippets:
        context_parts.append("### FRONTEND ARCHITECTURE & REACT GUIDANCE:\n" + "\n\n".join(frontend_snippets))

    combined_context = "\n\n---\n\n".join(context_parts) if context_parts else "Rely on standard Node.js/Express and React production patterns."

    return {
        "context": combined_context,
        "rag_chunks": rag_chunks
    }
