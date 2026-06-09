<div align="center">

# 🏛️ NYAYASHASTRA


</div>



## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [Multi-Agent Pipeline](#-multi-agent-pipeline)
- [API Reference](#-api-reference)
- [Database Schema](#-database-schema)
- [Environment Variables](#-environment-variables)
- [Disclaimer](#-disclaimer)

---

## 🎯 Overview

**NYAYASHASTRA** is an AI-powered legal assistant specifically designed for Indian law. It leverages a sophisticated multi-agent Retrieval-Augmented Generation (RAG) system to provide accurate, contextual, and verifiable legal information. The system specializes in:

- **Indian Penal Code (IPC)** - The colonial-era criminal code (1860)
- **Bhartiya Nyaya Sanhita (BNS)** - The new criminal code (2023)
- **IPC ↔ BNS Cross-Referencing** - Automatic mapping between old and new laws (213+ mappings)
- **Indian Regulatory Statutes** - Various civil and corporate laws

---

## ✨ Features

| Feature                         | Description                                                       |
| ------------------------------- | ----------------------------------------------------------------- |
| 🤖 **Multi-Agent Intelligence** | 7 specialized AI agents working in orchestrated pipeline          |
| ⚖️ **IPC ↔ BNS Mapping**        | 213+ automatic cross-references between old and new criminal laws |
| 🌐 **Bilingual Support**        | Full English and Hindi (हिंदी) language support                   |
| 📚 **Verified Citations**       | Links only to official government gazettes and sources            |
| 📄 **Document Analysis**        | Upload and summarize court orders, FIRs, and judgments            |
| 🏛️ **Case Law Intelligence**    | Supreme Court and High Court judgment retrieval                   |
| 🔍 **Semantic Search**          | Vector-based retrieval using ChromaDB for precise legal answers   |
| ⚡ **Real-time Processing**     | Live agent status updates with 3D visualization                   |
| 🎙️ **Voice Input**              | Speech-to-text support for queries in English and Hindi           |
| 📱 **Responsive Design**        | Works seamlessly on desktop and mobile devices                    |
| 💬 **Chat History**             | Persistent conversation history across sessions                   |
| 🎨 **3D Visualization**         | Interactive agent orchestration visualization using Three.js      |

---

## 🛠️ Tech Stack

### Frontend

| Technology                       | Purpose                 |
| -------------------------------- | ----------------------- |
| **React 18**                     | UI Framework            |
| **TypeScript**                   | Type Safety             |
| **Vite**                         | Build Tool & Dev Server |
| **TailwindCSS**                  | Styling                 |
| **Framer Motion**                | Animations              |
| **Three.js / React Three Fiber** | 3D Visualizations       |
| **Shadcn/ui**                    | UI Components           |
| **React Query**                  | Data Fetching & Caching |
| **React Router**                 | Client-side Routing     |

### Backend

| Technology                | Purpose                            |
| ------------------------- | ---------------------------------- |
| **FastAPI**               | REST API Framework                 |
| **Python 3.10+**          | Backend Language                   |
| **SQLAlchemy**            | ORM                                |
| **PostgreSQL / SQLite**   | Database                           |
| **ChromaDB**              | Vector Database                    |
| **LangChain**             | LLM Orchestration                  |
| **Groq API**              | Fast LLM Inference (Llama 3.3 70B) |
| **OpenAI API**            | Fallback LLM                       |
| **Sentence Transformers** | Text Embeddings                    |
| **Uvicorn**               | ASGI Server                        |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Landing   │  │    Chat     │  │ Comparison  │  │  Documents  │     │
│  │    Page     │  │  Interface  │  │    View     │  │   Upload    │     │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘     │
│                              │                                           │
│                    ┌─────────┴─────────┐                                │
│                    │   React Query     │                                │
│                    │   API Service     │                                │
│                    └─────────┬─────────┘                                │
└──────────────────────────────┼──────────────────────────────────────────┘
                               │ HTTP/REST
┌──────────────────────────────┼──────────────────────────────────────────┐
│                           BACKEND                                        │
│                    ┌─────────┴─────────┐                                │
│                    │    FastAPI        │                                │
│                    │   (CORS, Auth)    │                                │
│                    └─────────┬─────────┘                                │
│                              │                                           │
│         ┌────────────────────┼────────────────────┐                     │
│         │                    │                    │                     │
│  ┌──────┴──────┐  ┌─────────┴─────────┐  ┌──────┴──────┐              │
│  │   Chat      │  │    Statutes       │  │  Documents  │              │
│  │   Routes    │  │    Routes         │  │   Routes    │              │
│  └──────┬──────┘  └─────────┬─────────┘  └──────┬──────┘              │
│         │                   │                    │                     │
│  ┌──────┴───────────────────┴────────────────────┴──────┐              │
│  │              AGENT ORCHESTRATOR                       │              │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐    │              │
│  │  │ Query   │→│ Statute │→│  Case   │→│Regulatory│    │              │
│  │  │ Agent   │ │ Agent   │ │ Agent   │ │ Agent   │    │              │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘    │              │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐               │              │
│  │  │Citation │→│Summary  │→│Response │               │              │
│  │  │ Agent   │ │ Agent   │ │ Agent   │               │              │
│  │  └─────────┘ └─────────┘ └─────────┘               │              │
│  └───────────────────────────────────────────────────────┘              │
│                              │                                           │
│         ┌────────────────────┼────────────────────┐                     │
│         │                    │                    │                     │
│  ┌──────┴──────┐  ┌─────────┴─────────┐  ┌──────┴──────┐              │
│  │ PostgreSQL  │  │    ChromaDB       │  │  Groq/      │              │
│  │  Database   │  │  Vector Store     │  │  OpenAI     │              │
│  └─────────────┘  └───────────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

This section is organized by user type so people trying this repo from GitHub can choose the fastest path.

### 0) Prerequisites (All Users)

- **Git**
- **Node.js 18+**
- **Python 3.10+**

Verify tools:

```bash
git --version
node --version
python --version
```

Clone the repository:

```bash
git clone https://github.com/ancient-kid/NYAYASHASTRA.git
cd NYAYASHASTRA
```

### 1) Quick Demo User (Run Full App Locally)

Use this if you just want to run the project and try chat/comparison/doc features.

#### Step A: Start Backend

```bash
cd backend
python -m venv venv
```

Activate venv:

- **Windows PowerShell**

```powershell
.\venv\Scripts\Activate.ps1
```

- **Windows CMD**

```bat
venv\Scripts\activate.bat
```

- **macOS/Linux**

```bash
source venv/bin/activate
```

Install dependencies and configure env:

```bash
pip install -r requirements.txt
```

Copy env file:

- **Windows PowerShell**

```powershell
Copy-Item .env.example .env
```

- **macOS/Linux**

```bash
cp .env.example .env
```

Optional but recommended for better LLM quality:

- Add `GROQ_API_KEY` in `backend/.env`
- Optionally add `OPENAI_API_KEY` as fallback

Seed local legal data (first run only):

```bash
python -m app.seed_database
```

Run backend:

```bash
python -m uvicorn app.main:app --reload --port 8000
```

#### Step B: Start Frontend (new terminal)

```bash
# from repository root
npm install
```

Create root `.env` file:

```env
VITE_API_URL=http://localhost:8000
```

Run frontend:

```bash
npm run dev
```

#### Step C: Open App

| Service          | URL                        |
| ---------------- | -------------------------- |
| **Frontend**     | http://localhost:5173      |
| **API Docs**     | http://localhost:8000/docs |
| **ReDoc**        | http://localhost:8000/redoc |
| **Health Check** | http://localhost:8000/health |

### 2) Frontend-Only Contributor

Use this if you are working only on UI/UX and want fast iteration.

1. Start backend once using section **1) Quick Demo User**.
2. In root, run:

```bash
npm install
npm run dev
```

3. Run tests/lint as needed:

```bash
npm test
npm run lint
```

### 3) Backend/API-Only Contributor

Use this if you are building agents, APIs, retrieval, or database logic.

```bash
cd backend
python -m venv venv
# activate venv (see section 1)
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

API surface:

- Swagger docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 4) Common First-Run Notes

- First startup can be slow because embedding/vector dependencies may download models.
- If port `8000` is busy, run backend on another port and update `VITE_API_URL`.
- If port `5173` is busy, Vite picks another port automatically.
- SQLite and Chroma data are created locally during run/seed.

### 5) Stop Services

- Press `Ctrl + C` in each running terminal.

---

## 📁 Project Structure

```
NYAYASHASTRA/
├── 📁 backend/                    # FastAPI Backend
│   ├── 📁 app/
│   │   ├── 📁 agents/             # Multi-Agent System
│   │   │   ├── base.py            # Base agent class
│   │   │   ├── orchestrator.py    # Agent coordination
│   │   │   ├── query_agent.py     # Query understanding
│   │   │   ├── statute_agent.py   # Statute retrieval
│   │   │   ├── case_agent.py      # Case law retrieval
│   │   │   ├── regulatory_agent.py# Domain filtering
│   │   │   ├── citation_agent.py  # Citation verification
│   │   │   ├── summarization_agent.py
│   │   │   └── response_agent.py  # Response synthesis
│   │   ├── 📁 data/
│   │   │   ├── ipc_bns_chart.csv  # 250 IPC-BNS mappings
│   │   │   └── legal_seeds.py     # Data loader
│   │   ├── 📁 routes/
│   │   │   ├── chat.py            # Chat API endpoints
│   │   │   ├── statutes.py        # Statute endpoints
│   │   │   ├── documents.py       # Document upload
│   │   │   └── cases.py           # Case law endpoints
│   │   ├── 📁 services/
│   │   │   ├── llm_service.py     # Groq/OpenAI integration
│   │   │   ├── vector_store.py    # ChromaDB service
│   │   │   ├── chat_service.py    # Chat logic
│   │   │   ├── statute_service.py # Statute queries
│   │   │   └── case_service.py    # Case law queries
│   │   ├── config.py              # Settings management
│   │   ├── database.py            # DB connection
│   │   ├── models.py              # SQLAlchemy models
│   │   ├── schemas.py             # Pydantic schemas
│   │   ├── main.py                # FastAPI app
│   │   └── seed_database.py       # DB seeder
│   ├── requirements.txt
│   └── .env.example
│
├── 📁 src/                        # React Frontend
│   ├── 📁 components/
│   │   ├── ChatInterface.tsx      # Main chat UI
│   │   ├── Header.tsx             # Navigation header
│   │   ├── LandingPage.tsx        # Home page
│   │   ├── AgentOrchestration3D.tsx # 3D visualization
│   │   ├── AgentStatusPanel.tsx   # Agent status display
│   │   ├── EnhancedIPCBNSComparison.tsx
│   │   ├── CaseLawsPanel.tsx
│   │   ├── CitationsPanel.tsx
│   │   ├── DocumentUpload.tsx
│   │   └── 📁 ui/                 # Shadcn components
│   ├── 📁 pages/
│   │   ├── Index.tsx              # Dashboard
│   │   ├── Comparison.tsx         # IPC-BNS comparison
│   │   ├── Documents.tsx          # Document management
│   │   └── SignInPage.tsx
│   ├── 📁 services/
│   │   └── api.ts                 # API client
│   ├── 📁 hooks/
│   │   ├── useApi.ts              # API hooks
│   │   └── useChatContext.tsx     # Chat state
│   └── App.tsx
│
├── package.json
├── vite.config.ts
├── tailwind.config.ts
├── backend/scripts/               # Data ingestion and seeding scripts
└── README.md
```

---

## 🤖 Multi-Agent Pipeline

NYAYASHASTRA uses a sophisticated 7-agent pipeline to process legal queries:

```
User Query
    │
    ▼
┌──────────────────────────────────────────────────────────────────┐
│                     AGENT ORCHESTRATOR                            │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1️⃣ ┌─────────────────┐                                          │
│     │  Query Agent    │  • Language detection (EN/HI)            │
│     │                 │  • Domain classification                  │
│     │                 │  • Intent extraction                      │
│     └────────┬────────┘  • Query reformulation                   │
│              │                                                    │
│  2️⃣ ┌────────┴────────┐  3️⃣ ┌─────────────────┐                  │
│     │ Statute Agent   │     │  Case Agent     │                  │
│     │                 │     │                 │                  │
│     │ • IPC sections  │     │ • SC judgments  │                  │
│     │ • BNS sections  │     │ • HC judgments  │                  │
│     │ • Vector search │     │ • Landmark cases│                  │
│     └────────┬────────┘     └────────┬────────┘                  │
│              │                       │                            │
│              └───────────┬───────────┘                            │
│                          │                                        │
│  4️⃣ ┌────────────────────┴────────────────────┐                   │
│     │         Regulatory Agent                │                   │
│     │  • Jurisdiction filtering               │                   │
│     │  • Domain relevance scoring             │                   │
│     └────────────────────┬────────────────────┘                   │
│                          │                                        │
│  5️⃣ ┌────────────────────┴────────────────────┐                   │
│     │          Citation Agent                 │                   │
│     │  • Source verification                  │                   │
│     │  • Official gazette links               │                   │
│     └────────────────────┬────────────────────┘                   │
│                          │                                        │
│  6️⃣ ┌────────────────────┴────────────────────┐                   │
│     │       Summarization Agent               │                   │
│     │  • Key points extraction                │                   │
│     │  • Bilingual summaries                  │                   │
│     └────────────────────┬────────────────────┘                   │
│                          │                                        │
│  7️⃣ ┌────────────────────┴────────────────────┐                   │
│     │         Response Agent                  │                   │
│     │  • Final answer synthesis               │                   │
│     │  • Citation formatting                  │                   │
│     │  • Hindi translation (if needed)        │                   │
│     └────────────────────┬────────────────────┘                   │
│                          │                                        │
└──────────────────────────┼────────────────────────────────────────┘
                           │
                           ▼
              📋 Legal Response with Citations
```

---

## 📡 API Reference

### Chat Endpoints

| Method | Endpoint                  | Description                        |
| ------ | ------------------------- | ---------------------------------- |
| `POST` | `/api/chat`               | Send a legal query                 |
| `POST` | `/api/chat/stream`        | Stream response with agent updates |
| `GET`  | `/api/chat/history`       | Get chat history                   |
| `GET`  | `/api/chat/sessions/{id}` | Get specific session               |

### Statute Endpoints

| Method | Endpoint                      | Description             |
| ------ | ----------------------------- | ----------------------- |
| `GET`  | `/api/statutes`               | List all statutes       |
| `GET`  | `/api/statutes/search`        | Search statutes         |
| `GET`  | `/api/statutes/section/{num}` | Get specific section    |
| `GET`  | `/api/statutes/comparison`    | IPC-BNS comparison list |

### Document Endpoints

| Method | Endpoint                      | Description             |
| ------ | ----------------------------- | ----------------------- |
| `POST` | `/api/documents/upload`       | Upload document         |
| `GET`  | `/api/documents/status/{id}`  | Check processing status |
| `GET`  | `/api/documents/{id}/summary` | Get document summary    |

### Case Endpoints

| Method | Endpoint            | Description      |
| ------ | ------------------- | ---------------- |
| `GET`  | `/api/cases`        | List case laws   |
| `GET`  | `/api/cases/search` | Search cases     |
| `GET`  | `/api/cases/{id}`   | Get case details |

---

## 🗄️ Database Schema

### Core Tables

```sql
-- Statutes (IPC/BNS sections) - 452 records
statutes
├── id (PK)
├── section_number
├── act_code (IPC, BNS)
├── act_name
├── title_en / title_hi
├── content_en / content_hi
├── domain
├── punishment_description
├── is_bailable / is_cognizable
└── embedding_id (→ ChromaDB)

-- IPC-BNS Mappings - 213 records
ipc_bns_mappings
├── id (PK)
├── ipc_section_id (FK)
├── bns_section_id (FK)
├── mapping_type (exact, modified, merged, split)
├── changes (JSON)
├── punishment_changed
└── old_punishment / new_punishment

-- Case Laws - 8+ landmark cases
case_laws
├── id (PK)
├── case_number
├── case_name / case_name_hi
├── court (supreme_court, high_court)
├── judgment_date
├── summary_en / summary_hi
├── citation_string
└── is_landmark

-- Chat Sessions & Messages
chat_sessions → chat_messages
```

---

## ⚙️ Environment Variables

Create a `.env` file in the `backend/` directory (you can copy from `backend/.env.example`):

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=true
CORS_ORIGINS=http://localhost:5173,http://localhost:8080,http://localhost:8081

# Database (SQLite default; PostgreSQL optional)
DATABASE_URL=sqlite:///./nyayashastra.db
# DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Vector Database
CHROMA_PERSIST_DIR=./chroma_db
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

# LLM Configuration (Groq - Primary)
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=meta-llama/llama-4-scout-17b-16e-instruct

# OpenAI (Fallback)
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4-turbo-preview

# Optional
HF_TOKEN=hf_xxx
```

Create a `.env` in root for frontend:

```env
VITE_API_URL=http://localhost:8000
```

Minimum setup to run locally:

- `backend/.env`: set at least `GROQ_API_KEY` (recommended)
- `/.env`: set `VITE_API_URL=http://localhost:8000`

---


## ⚠️ Disclaimer

> **IMPORTANT**: This service is for **informational purposes only** and does **not constitute legal advice**.
>
> The information provided by NYAYASHASTRA should not be considered as a substitute for professional legal counsel. Always consult a qualified legal professional for specific legal matters.
>
> While we strive for accuracy, laws and their interpretations can change. Users should verify all information with official government sources.


