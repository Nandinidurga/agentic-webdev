# Project Implementation Plan: Agent-based LLM for Web Application Development

This document outlines the step-by-step implementation plan for building the Agent-based Web Development platform based on the `architecture_and_workflow.md` design.

## User Review Required

> [!IMPORTANT]
> **RAG Knowledge Base Source:** The plan proposes cloning community-curated GitHub repositories (like `HarshVadaliya/tech-books-library` or `EbookFoundation/free-programming-books`) to obtain Web Development PDFs for the RAG knowledge base. Please confirm if this approach is acceptable, or if you have specific internal PDFs/repositories you prefer to use.

> [!CAUTION]
> **Execution Sandbox:** The architecture requires a sandbox for the Coder Agent to test code safely. The plan assumes we will set up a local **Docker-based** sandbox for initial development. Please confirm if you have Docker installed and running on your system, or if you prefer using a cloud sandbox like E2B.

## Open Questions

1. **LLM Provider:** We are using Gemini 2.5 Flash as per the architecture. Do you have an API key ready, and should we store it in a `.env` file in the root directory?
2. **Frontend Styling:** Should the Next.js frontend (the IDE Interface) use standard CSS, or would you like to incorporate Tailwind CSS for rapid styling (despite the general guideline preferring Vanilla CSS, Tailwind is common for Next.js dashboards)?

## Proposed Changes

We will construct the project in four main phases.

### Phase 1: Knowledge Base Setup (RAG)
We will create a local repository for our RAG data.
- **[NEW]** `knowledge_base/` directory.
- **Action:** Clone/download web development PDF resources (React, Next.js, Python, CSS) from open-source GitHub repositories into this folder.

### Phase 2: Project Scaffolding
Setting up the core directories for the Backend (Agents) and Frontend (IDE UI).

#### Backend (Python / LangGraph)
- **[NEW]** `backend/` directory.
- **[NEW]** `backend/requirements.txt`: (langgraph, chromadb, fastapi, google-generativeai, langchain, pypdf).
- **[NEW]** `backend/main.py`: FastAPI entry point.
- **[NEW]** `backend/rag_ingest.py`: Script to process PDFs from `knowledge_base/` and store them in ChromaDB.

#### Frontend (Next.js)
- **[NEW]** `frontend/` directory.
- **Action:** Run `npx create-next-app@latest frontend` to scaffold the Next.js application.
- **[NEW]** `frontend/components/Editor.jsx`: Monaco Editor component.

### Phase 3: Core Agent Implementation
Implementing the "Brains" in the backend using LangGraph.
- **[NEW]** `backend/agents/orchestrator.py`
- **[NEW]** `backend/agents/knowledge.py`
- **[NEW]** `backend/agents/coder.py`
- **[NEW]** `backend/agents/reviewer.py`
- **[NEW]** `backend/graph.py`: LangGraph state machine linking the agents together.

### Phase 4: Sandbox Environment
Setting up the secure execution "Hands".
- **[NEW]** `sandbox/Dockerfile`: A container image with Node.js and Python pre-installed for the Coder Agent to run generated code.

## Verification Plan

### Automated Tests
- Run `python backend/rag_ingest.py` to ensure PDFs are successfully chunked and loaded into ChromaDB without errors.
- Run `npm run lint` and `npm run build` in the frontend directory to ensure the Next.js app is structurally sound.

### Manual Verification
- Start the FastAPI backend and query the RAG endpoint manually to see if relevant context from the PDFs is returned.
- Start the Next.js frontend (`npm run dev`) and verify the UI loads correctly and can send a prompt to the backend.
