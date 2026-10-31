"""
knowledge.py - Dual-domain RAG retrieval agent for full-stack engineering.

Architecture:
- Singleton Chroma & HuggingFaceEmbeddings initialized once at module startup.
- Uses modern `langchain-chroma` package.
- Domain-isolated metadata filtering (`domain="backend"` and `domain="frontend"`).
- Configurable top-k (`RAG_K`) and relevance score thresholding (`RAG_SCORE_THRESHOLD`).
- Provides ranked, scored chunks directly to state for token-budgeted prompt construction.
"""

import os
from typing import Optional, List, Dict, Any, Tuple
from dotenv import load_dotenv

load_dotenv()

# Module-level singletons for embeddings and Chroma vectorstore
_EMBEDDINGS = None
_VECTORSTORE = None
_INITIALIZED = False

CHROMA_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chroma_db"))


def get_vectorstore():
    """
    Module singleton provider for Chroma vector store and HuggingFace embeddings.
    Builds embeddings model and connects to local Chroma DB once at startup.
    """
    global _EMBEDDINGS, _VECTORSTORE, _INITIALIZED
    if _INITIALIZED:
        return _VECTORSTORE

    _INITIALIZED = True
    if not os.path.exists(CHROMA_DB_PATH):
        return None

    try:
        from langchain_huggingface import HuggingFaceEmbeddings
        from langchain_chroma import Chroma

        _EMBEDDINGS = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        _VECTORSTORE = Chroma(
            persist_directory=CHROMA_DB_PATH,
            embedding_function=_EMBEDDINGS,
            collection_name="langchain"
        )
        return _VECTORSTORE
    except Exception as err:
        print(f"Warning: Failed to initialize Chroma singleton: {err}", flush=True)
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
    score_threshold = float(os.getenv("RAG_SCORE_THRESHOLD", "0.0"))

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

    # 2. Retrieve Frontend-specific documentation (React hooks, state, preview stores, forms)
    frontend_query = f"React components hooks state layout UI JSX Tailwind {prompt} {plan[:300]}"
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

    # Sort chunks globally by score descending
    rag_chunks.sort(key=lambda c: c["score"], reverse=True)

    backend_context = "\n---\n".join(backend_snippets) if backend_snippets else "Standard Express patterns applied."
    frontend_context = "\n---\n".join(frontend_snippets) if frontend_snippets else "Standard React preview patterns applied."

    context = f"""=== BACKEND REFERENCE DOCUMENTATION (RAG) ===
{backend_context}

=== FRONTEND REFERENCE DOCUMENTATION (RAG) ===
{frontend_context}"""

    print(f"RAG Knowledge Agent retrieved {len(backend_matches)} backend and {len(frontend_matches)} frontend chunks (threshold: {score_threshold}).", flush=True)

    return {
        "context": context,
        "rag_chunks": rag_chunks
    }
