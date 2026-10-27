# Agentic IDE: Full-Stack Architecture & Cognitive Workflow

> [!NOTE]
> **Vision:** An autonomous full-stack AI web development engineering platform that translates natural language prompts into complete, verified, live-previewable web applications featuring both a **Node.js / Express.js REST API Backend** and a **React Interactive Frontend**.

---

## 1. System Architecture (The "Brain & Hands")

The architecture integrates a cyclical multi-agent cognitive graph (LangGraph), a dual-provider resilient LLM engine, a dual-domain Vector Knowledge Base (ChromaDB), an in-browser isolated execution sandbox (CodeSandbox Sandpack), and a high-performance Monaco Editor.

### High-Level Architecture Diagram

```mermaid
flowchart TD
    User([User Natural Language Prompt]) --> UI[Next.js 16 Full-Stack Studio\n• Sandpack Live Preview\n• Monaco Backend Inspector\n• Interactive REST API Tester\n• JSZip Project Exporter]
    
    UI -->|POST /generate| Gateway[FastAPI Backend Gateway :8000]

    subgraph Cognitive Layer - LangGraph Multi-Agent Workflow
        Orchestrator[Orchestrator Agent\n• Architectural Blueprint\n• Structured REST API Spec]
        Knowledge[Dual RAG Knowledge Agent\n• ChromaDB Semantic Search\n• React + Express Docs]
        Coder[Coder Agent\n• Express Server + CRUD Routes\n• React UI Components & Styles\n• Dual-Mode API Client]
        Reviewer[Reviewer & Auto-Healer Agent\n• Static Syntax & Route Check\n• Runtime Guard Injection\n• Iteration Bounded Loop]
    end

    subgraph LLM Resilience Engine
        LLMFactory[Resilient LLM Factory]
        Groq[Primary: Groq Cloud\nGPT-OSS-20b / Llama-3.3-70b\nAutomated Backoff Retry]
        Gemini[Fallback: Google Gemini\nGemini 1.5 Flash\nDeep Context Reasoning]
    end

    subgraph Knowledge & Memory Layer
        Chroma[(ChromaDB Vector Store\nall-MiniLM-L6-v2 Embeddings)]
        FrontendDocs[React 19 Official Documentation]
        BackendDocs[Express.js & REST Best Practices]
    end

    Gateway --> Orchestrator
    Orchestrator --> Knowledge
    Knowledge <--> Chroma
    FrontendDocs --> Chroma
    BackendDocs --> Chroma
    Knowledge --> Coder
    Coder --> Reviewer
    Reviewer -->|Self-Healing Loop if Critical Errors & Iteration < 3| Coder
    Reviewer --> Gateway

    Orchestrator -.-> LLMFactory
    Coder -.-> LLMFactory
    LLMFactory --> Groq
    Groq -.->|On 429 TPM Rate Limit| Gemini

    Gateway -->|Full-Stack Files & Specs| UI
    UI --> Sandpack[Live In-Browser Sandpack Sandbox]
    UI --> ApiInspector[Interactive REST API Tester with Custom Payloads]
    UI --> BackendEditor[Monaco Multi-File Source Inspector]
    UI --> ZipExport[JSZip Full-Stack Runnable Bundle]
```

---

## 2. The 4 Cognitive Agents

### 1. Orchestrator Agent (The System Architect)
* **Responsibility:** Deconstructs user requirements into a comprehensive technical blueprint and a structured REST API specification.
* **Outputs:** 
  * Architectural overview and feature roadmap.
  * Formal API route specifications: HTTP methods (`GET`, `POST`, `PUT`, `DELETE`), paths (e.g. `/api/items`), route descriptions, and sample request/response payloads.

### 2. Dual RAG Knowledge Agent (The Technical Researcher)
* **Responsibility:** Retrieves validated, gold-standard code patterns from the local vector database across two domains:
  * **Frontend:** React 19 hooks, component lifecycles, and Tailwind styling patterns.
  * **Backend:** Express.js routing, in-memory data modeling, CORS configuration, error-handling middleware, and REST status codes.
* **Vector Store:** ChromaDB with local HuggingFace `sentence-transformers/all-MiniLM-L6-v2` embeddings (zero external latency and zero cost).

### 3. Coder Agent (The Full-Stack Software Engineer)
* **Responsibility:** Generates both the backend server and frontend client as a unified, cohesive JSON file tree:
  * `/server.js`: Complete Node.js/Express.js backend with seed data, REST routes, CORS middleware, and `/api/health`.
  * `/server/package.json`: Backend package descriptor specifying Express and CORS dependencies.
  * `/services/api.js`: Intelligent dual-mode API client that attempts live HTTP connection to `http://localhost:5000`, with graceful fallback to an in-memory preview store inside Sandpack.
  * `/App.js`: Complete, interactive React component with search, filtering, creation/editing forms, metrics, and state badges.
  * `/styles.css`: Modern CSS styling with smooth micro-animations, glassmorphism cards, and responsive layouts.
  * `/package.json`: Client package descriptor specifying `lucide-react`.

### 4. Reviewer & Auto-Healer Agent (The QA Engineer & Healer)
* **Responsibility:** Analyzes all generated files for correctness, compliance with the API specification, and runtime safety.
* **Auto-Healing Pipeline:**
  * Detects missing routes or unstarted servers in `/server.js`.
  * Automatically injects defensive runtime guards into React code (`(items || []).map(...)`, `(Number(val) || 0).toFixed(2)`).
  * Auto-heals uninitialized `useState()` hooks to `useState([])`.
  * Standardizes single-quoted `package.json` files to strictly valid double-quoted JSON.
  * Strictly bounds retry iterations to at most 3 cycles to guarantee deterministic termination.

---

## 3. Full-Stack Export Architecture

When users export the project, `JSZip` structures the bundle into standard, modular development environments:

```
agentic-fullstack-app.zip
├── README.md                 # Universal startup instructions & API documentation
├── server/                   # Node.js / Express Backend
│   ├── server.js             # REST API server & CORS configuration
│   └── package.json          # Express and CORS dependencies
└── client/                   # React Frontend Client
    ├── package.json          # React, ReactDOM, and icon dependencies
    └── src/
        ├── App.js            # Main interactive UI application
        ├── styles.css        # Responsive styling and glassmorphism themes
        └── services/
            └── api.js        # Dual-mode API client (live HTTP + fallback)
```

---

## 4. The 3-Layer Defensive Immunity System

To eliminate runtime crashes in Sandpack (such as `Cannot read properties of undefined (reading 'map')`), the system enforces three independent defense perimeters:

```mermaid
flowchart TD
    subgraph Layer 3: Coder Prompt Hardening
        L3A[Strict Prompt Rules] --> L3B[Collection state MUST be useState array]
        L3A --> L3C[Collections MUST use defensive map/filter]
        L3A --> L3D[API functions MUST return mock arrays in catch block]
    end

    subgraph Layer 2: Server-Side Reviewer Auto-Healer
        L2A[heal_frontend_code] --> L2B[Replaces bare useState with useState array]
        L2A --> L2C[Wraps bare array methods with var or empty array]
        L2A --> L2D[Wraps toFixed with Number conversion fallback]
        L2A --> L2E[Converts single-quoted package.json to double quotes]
        L2A --> L2F[Tracks iteration bounds to prevent infinite loops]
    end

    subgraph Layer 1: Client-Side Sandpack Sanitizer
        L1A[page.tsx Filter & Sanitizer] --> L1B[Excludes backend server files from Sandpack]
        L1A --> L1C[Robust parsePackageJson with regex fallback]
        L1A --> L1D[Client-side array and number guard regex]
        L1A --> L1E[Fallback mock API store injection if missing]
    end

    Layer 3 --> Layer 2 --> Layer 1 --> Sandbox[100% Crash-Free Sandpack Live Preview]
```

---

## 5. Technology Stack Summary

| Component | Technology | Role |
|:---|:---|:---|
| **Frontend IDE** | Next.js 16 (App Router), React 19, TypeScript | Reactive developer studio shell |
| **Styling** | Vanilla CSS + TailwindCSS Utilities | Modern dark-mode UI with sleek glassmorphism |
| **In-Browser Sandbox** | `@codesandbox/sandpack-react` | Zero-latency, browser-isolated React bundler |
| **Code Editor** | Monaco Editor (`@monaco-editor/react`) | Professional syntax highlighting & source inspection |
| **Backend Gateway** | FastAPI, Uvicorn (Python 3.12) | High-concurrency async REST server on port 8000 |
| **Agent Orchestration** | LangGraph & LangChain Core | Cyclical, multi-node state graph with conditional branching |
| **Primary LLM** | Groq Cloud (`openai/gpt-oss-20b`, `llama-3.3-70b`) | Ultra-fast token generation (~3s) with automated backoff retry |
| **Fallback LLM** | Google Gemini (`gemini-1.5-flash`) | High-capacity fallback reasoning engine |
| **Vector Database** | ChromaDB | Local persistent store for technical documentation |
| **Embedding Engine** | HuggingFace `sentence-transformers/all-MiniLM-L6-v2` | Zero-cost, local semantic vectorizer |
| **Export Engine** | `jszip` | On-the-fly packaging of runnable full-stack zip distributions |
| **Feedback UX** | `canvas-confetti` | Visual celebration upon successful generation |

---

## 6. Execution & Sandbox Strategy

* **In-Browser Sandpack Sandbox:** Client-side React code executes inside an isolated iframe managed by Sandpack. No local Docker installation is required.
* **Dual-Mode Client Architecture:** `/services/api.js` enables the generated app to run out-of-the-box inside the browser sandbox using in-memory mock data, while instantly connecting to `http://localhost:5000` when the user starts the local Express server.
* **Zero Backend Bundle Pollution:** Backend files (`/server.js`, `/server/package.json`) are filtered out before reaching Sandpack, preventing Node.js module resolution errors in the browser.
* **Interactive Endpoint Testing:** The studio allows direct parameter substitution (e.g. `:id` -> `1`) and editable JSON payloads for `POST`/`PUT`/`PATCH` endpoints.
