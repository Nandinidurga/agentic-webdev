# Agentic IDE: Full-Stack Agent-Based Web App Developer

Agentic IDE is an advanced web development platform that converts natural language prompts into fully functional, live-previewable web applications. It orchestrates multiple specialized AI agents under the hood, utilizing a self-healing LangGraph workflow and Retrieval-Augmented Generation (RAG) for up-to-date documentation.

---

## 🚀 Plan of Action & Roadmap

We are implementing this project in structured phases. Below is the current implementation status and the roadmap ahead.

### Phase 1: Foundation & Scaffolding (Completed)
- [x] Create project layout (`backend/` and `frontend/`).
- [x] Configure standard root `.gitignore` and local environment file `.env`.
- [x] Scaffold Next.js frontend structure with Sandpack React workspace integration.
- [x] Scaffold FastAPI backend endpoints and LangGraph environment configurations.

### Phase 2: LangGraph Core Flow (Completed)
- [x] Define LangGraph agent state (`AgentState`) to hold prompt, plan, files, errors, and metadata.
- [x] Implement **Orchestrator Agent** to break down user prompt into clear actionable technical plans.
- [x] Implement **RAG Knowledge Agent** stub for document retrieval integration.
- [x] Implement **Coder Agent** to write actual codes, returning structured JSON files.
- [x] Implement **Reviewer Agent** with self-healing feedback loop capability.
- [x] Wire state nodes into a compiler-ready LangGraph workflow.

### Phase 3: RAG Database Populating (Active)
- [ ] Clone open-source Web Dev reference libraries (Next.js, Tailwind, React, FastAPI).
- [ ] Implement `rag_ingest.py` to chunk PDFs/documentation and load them into ChromaDB.
- [ ] Wire vector database retrieval logic directly into the **RAG Knowledge Agent** to feed high-fidelity templates to the Coder.

### Phase 4: Dynamic Sandbox & Execution (Next Steps)
- [ ] Connect the Reviewer Agent to an active runtime environment (like local Docker containers or the E2B Code Interpreter API).
- [ ] Execute generated code live within the sandbox during generation to capture build errors (e.g. syntax, compile, import failures).
- [ ] Feed stderr back to Coder Agent for iterative self-healing before approval.

### Phase 5: Hosting & Production Deployments
- [ ] Connect Orchestrator to Vercel/Netlify hosting APIs.
- [ ] Return live preview URLs of completed applications directly to the interactive Next.js editor.

---

## 🛠️ System Architecture

```mermaid
graph TD
    User([User]) --> |"Natural Language Prompt"| UI[IDE Interface\nNext.js + Monaco]
    UI --> Orchestrator
    
    subgraph Cognitive Layer - LangGraph Agents
        Orchestrator[Orchestrator Agent\n'The Manager']
        Knowledge[RAG-Knowledge Agent\n'The Researcher']
        Coder[Coder Agent\n'The Developer']
        Reviewer[Reviewer/Debugger Agent\n'The QA']
    end
    
    subgraph Infrastructure & Memory
        VectorDB[(Vector DB\nChromaDB)]
        Sandbox[Execution Sandbox\nDocker/E2B]
    end
    
    Orchestrator --> |Task Breakdown| Knowledge
    Orchestrator --> |Assigns Tasks| Coder
    
    Knowledge <--> |Query & Retrieve Docs| VectorDB
    Knowledge --> |Gold Standard Snippets| Coder
    
    Coder --> |Writes Code| Sandbox
    Sandbox --> |Execution Logs & Errors| Reviewer
    Reviewer --> |Self-Healing Loops| Coder
    Reviewer --> |Approval| Orchestrator
    
    Orchestrator --> |Live Preview Code| UI
```

1. **Orchestrator Agent:** The "Manager" that handles user intent, splits requirements into code tasks, and maintains overall state.
2. **RAG-Knowledge Agent:** The "Researcher" that fetches the correct syntax blocks and APIs from the local Vector DB.
3. **Coder Agent:** The "Developer" that builds raw React and HTML/JS file structures in a structured format.
4. **Reviewer Agent:** The "QA" that runs the generated code inside a sandbox, captures issues, and teaches the Coder how to fix them recursively.

---

## 💻 Tech Stack

- **Frontend:** Next.js (React), TailwindCSS, CodeSandbox Sandpack (for in-browser preview & file explorer)
- **Backend Framework:** FastAPI (Python 3.10+)
- **Agent Orchestration:** LangGraph & LangChain
- **AI Models:** Gemini 2.5 Flash (via `langchain-google-genai`)
- **Knowledge Memory:** ChromaDB (Vector Database) for document retrieval

---

## 🏃 Run Local Setup

### Prerequisites
- Node.js (v18+)
- Python (v3.10+)

### 1. Configure Environments
Create a `.env` file at the root directory of the project:
```env
GOOGLE_API_KEY=your_gemini_api_key
HF_TOKEN=your_huggingface_token
E2B_API_KEY=your_optional_e2b_api_key
```

### 2. Launch Backend Server
```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\Activate.ps1
# On Unix:
source venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 3. Launch Frontend Server
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) to view the web application.
