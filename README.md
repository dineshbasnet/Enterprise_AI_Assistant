# Enterprise AI Assistant

> A multi-agent AI platform for organizational knowledge retrieval, intelligent document processing, and support ticket management — built with LangGraph, FastAPI, PaddleOCR, and React.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Agents](#agents)
- [API Reference](#api-reference)
- [Development Methodology](#development-methodology)
- [Team](#team)
- [License](#license)

---

## Overview

The **Organizational Intelligent AI Assistant** is a minor project built for Kathford International College of Engineering and Management, affiliated to Tribhuvan University. It provides a single unified AI platform embedded directly into an organization's website, enabling users — students, employees, and staff — to:

- Ask questions and get grounded, cited answers from organizational knowledge
- Upload documents and have them automatically OCR-processed, field-extracted, and submitted as verified forms
- Report problems that escalate intelligently into routed support tickets
- Provide feedback that feeds sentiment analysis and an analytics dashboard

All three capabilities are orchestrated by a **LangGraph-based agent graph** that maintains shared state across agents rather than treating them as isolated pipelines.

---

## Features

| Feature | Description |
|---|---|
| **RAG-based Q&A** | Retrieval-Augmented Generation using pgvector semantic search, reranking, and LLM grounding |
| **Intelligent Document Processing** | PaddleOCR text extraction → LayoutLMv3 field understanding → confidence-gated human verification |
| **Support Ticket Management** | Confidence-check branching: high-confidence queries answered directly, low-confidence ones escalate to department-routed tickets |
| **Sentiment Analysis** | RoBERTa-based sentiment scoring on post-resolution feedback |
| **Analytics Dashboard** | Aggregated ticket trends, response quality metrics, and sentiment over time |
| **Embedded Chat Widget** | React component embeddable on any organizational webpage |
| **Human-in-the-Loop** | Verification queue for low-confidence field extractions — only flagged fields, not whole documents |

---

## System Architecture

```
User
 │
 ▼
Organization Website
 │
 ▼
Embedded AI Widget  (React)
 │
 ▼
Auth Gateway  (JWT + role check)
 │
 ▼
Main Chatbot Layer  (session, intent routing)
 │
 ▼
Agent Orchestrator  (LangGraph — shared state graph)
 ├──► Knowledge Agent  →  RAG Retrieval → pgvector → LLM → Grounded Response
 ├──► Document Agent   →  OCR → Field Extraction → [Confidence Check] → Form Generation → Submission
 └──► Support Agent    →  [Confidence Check] → Direct Answer  OR  Ticket → Department Routing → Human Agent
                                                                    │
                                                              Feedback → Sentiment Analysis → Analytics
```

All agents share a common infrastructure layer:
- **PostgreSQL + pgvector** — relational data and vector embeddings
- **LLM Engine** — grounding and generation
- **OCR Engine** — PaddleOCR deployed as a standalone microservice

---

## Tech Stack

### Frontend
- **React.js** — web interface and embeddable chat widget
- **Vite** — build tooling

### Backend
- **FastAPI** — REST API layer
- **LangGraph** — multi-agent orchestration with shared `AgentState`
- **LangChain** — LLM application framework

### AI / ML
- **PaddleOCR** — optical character recognition (CPU build, isolated microservice)
- **LayoutLMv3** — document layout understanding and field extraction
- **pgvector** — vector similarity search for RAG retrieval
- **RoBERTa** — sentiment analysis on feedback

### Database
- **PostgreSQL** — primary relational database
- **pgvector extension** — stores and queries document chunk embeddings

### Infrastructure
- **Docker + Docker Compose** — containerised local development
- **Alembic** — database migrations

---

## Project Structure

```
organizational-ai-assistant/
│
├── README.md
├── .env
├── .gitignore
├── docker-compose.yml
│
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── ChatWidget/          # embeddable chat widget
│       │   ├── DocumentUpload/
│       │   ├── TicketForm/
│       │   └── Dashboard/           # analytics dashboard
│       ├── pages/
│       └── services/                # API call wrappers
│
├── backend/
│   ├── main.py                      # FastAPI entry point
│   ├── api/                         # route handlers only
│   │   ├── chat.py
│   │   ├── documents.py
│   │   ├── tickets.py
│   │   └── feedback.py
│   ├── agents/
│   │   ├── state.py                 # shared AgentState (avoids circular imports)
│   │   ├── orchestrator.py          # LangGraph graph definition
│   │   ├── knowledge_agent.py
│   │   ├── document_agent.py
│   │   └── support_agent.py
│   ├── services/                    # business logic
│   │   ├── rag_service.py
│   │   ├── ocr_service.py
│   │   ├── llm_service.py
│   │   ├── ticket_service.py
│   │   ├── sentiment_service.py
│   │   └── form_service.py
│   ├── models/                      # SQLAlchemy ORM models
│   ├── schemas/                     # Pydantic request/response schemas
│   ├── db/
│   │   ├── session.py
│   │   └── migrations/
│   ├── core/
│   │   ├── config.py                # Pydantic Settings
│   │   └── auth.py                  # JWT verification, role checks
│   └── tests/
│
├── ocr_service/                     # standalone PaddleOCR microservice
│   ├── main.py                      # POST /ocr
│   ├── paddle_ocr.py
│   └── Dockerfile
│
├── knowledge_base/
│   ├── documents/                   # source PDFs and policy documents
│   └── ingest.py                    # chunking → embedding → pgvector upsert
│
└── docs/
    ├── architecture.svg
    └── api_reference.md
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker and Docker Compose
- PostgreSQL 15+ with pgvector extension

### 1. Clone the repository

```bash
git clone https://github.com/<your-org>/organizational-ai-assistant.git
cd organizational-ai-assistant
```

### 2. Set up environment variables

```bash
cp .env.example .env
# Edit .env with your values — see Environment Variables section below
```

### 3. Start all services with Docker Compose

```bash
docker-compose up --build
```

This starts:
- `backend` — FastAPI on `http://localhost:8000`
- `frontend` — React on `http://localhost:5173`
- `ocr_service` — PaddleOCR microservice on `http://localhost:8001`
- `postgres` — PostgreSQL with pgvector on port `5432`

### 4. Run database migrations

```bash
cd backend
alembic upgrade head
```

### 5. Ingest organizational knowledge base

```bash
cd knowledge_base
python ingest.py --source documents/
```

### 6. Run without Docker (development)

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev

# OCR Service
cd ocr_service
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

---

## Environment Variables

Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/oai_assistant

# LLM
ANTHROPIC_API_KEY=your_anthropic_api_key
AZURE_AI_ENDPOINT=your_azure_ai_foundry_endpoint
AZURE_AI_KEY=your_azure_ai_key

# JWT Auth
SECRET_KEY=your_jwt_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# OCR Service
OCR_SERVICE_URL=http://localhost:8001

# Confidence threshold
CONFIDENCE_THRESHOLD=0.75

# Embedding model
EMBEDDING_MODEL=text-embedding-3-small
```

---

## Agents

### Knowledge Agent

Handles all question-answering requests using Retrieval-Augmented Generation.

**Flow:** User query → intent detection → embedding → pgvector top-k retrieval → reranking → LLM generation grounded on retrieved chunks → cited response

**Key files:** `agents/knowledge_agent.py`, `services/rag_service.py`

---

### Document Agent

Handles document uploads through an intelligent processing pipeline with confidence-gated human verification.

**Flow:** Document upload → PaddleOCR extraction → LayoutLMv3 field understanding → per-field confidence scoring → **if high confidence**: auto-accept to DB; **if low confidence**: human verification queue → dynamic form generation → user approval → submission

**Key files:** `agents/document_agent.py`, `services/ocr_service.py`, `services/form_service.py`

> **Design decision:** Human verification applies only to low-confidence fields, not entire documents. This prevents the verification queue from becoming a bottleneck during high-volume periods such as admission season.

---

### Support Agent

Handles problem reports and support queries with confidence-gated escalation.

**Flow:** User problem → chatbot attempts resolution → confidence check → **if high**: direct answer; **if low**: ticket creation → department routing → human agent → post-resolution feedback → sentiment analysis

**Key files:** `agents/support_agent.py`, `services/ticket_service.py`, `services/sentiment_service.py`

> **Design decision:** Ticket deduplication checks whether an open ticket already exists for the session before creating a new one. Negative post-resolution sentiment escalates the existing ticket rather than spawning a duplicate.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chat` | Send a message to the AI assistant |
| `POST` | `/api/documents/upload` | Upload a document for processing |
| `GET` | `/api/documents/{id}` | Get extracted fields for a document |
| `PUT` | `/api/documents/{id}/approve` | Approve and submit extracted form |
| `GET` | `/api/tickets` | List all tickets (admin) |
| `POST` | `/api/tickets` | Create a support ticket |
| `GET` | `/api/tickets/{id}` | Get ticket status |
| `POST` | `/api/feedback` | Submit post-resolution feedback |
| `GET` | `/api/analytics/dashboard` | Get analytics summary (admin) |
| `POST` | `/ocr` | *(OCR service)* Extract text from image/PDF |

Full API documentation available at `http://localhost:8000/docs` (Swagger UI) when running locally.

---

## Development Methodology

This project follows an **Agile development methodology** with iterative 6-sprint cycles:

| Sprint | Phase | Deliverable |
|---|---|---|
| 1 | Plan | Requirements, knowledge base sources, repo setup |
| 2 | Design | System architecture, DB schema, LangGraph state design, API contracts |
| 3 | Develop | RAG pipeline, OCR pipeline, ticket module, FastAPI + React frontend |
| 4 | Test | Unit tests per agent, integration tests, OCR accuracy validation |
| 5 | Review | Supervisor evaluation, confidence threshold tuning, UI feedback |
| 6 | Release | Final deployment, documentation, demo to panel |

---

## Team

| Name | Role |
|---|---|
| Dinesh Basnet | Backend & Agent Orchestration |
| Aaditya Prasad Ghimire | Document Processing & OCR Pipeline |
| Krishna Kusiyait Yadav | Frontend & Chat Widget |
| Ravi Shiwakoti | Support Agent & Analytics |

**Department of Computer and Electronics & Communication Engineering**
Kathford International College of Engineering and Management
Affiliated to Tribhuvan University

---

## License

This project is submitted as a minor project proposal for academic evaluation at Tribhuvan University. All rights reserved by the authors.

---

*Built with LangGraph · FastAPI · PaddleOCR · pgvector · React*