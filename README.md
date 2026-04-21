# CalendarOps: Agentic Personal Scheduler

An autonomous scheduling assistant that connects to your Google Calendar and uses an open-source LLM to reason about your schedule in natural language. You can ask it things like "what do I have tomorrow?" or "block an hour for the gym after my last class" and it will read your calendar, reason about the request, and write back to it — with your approval.

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Running the App](#running-the-app)
- [How It Works](#how-it-works)
- [Agent Rules](#agent-rules)
- [Implementation Phases](#implementation-phases)

---

## Overview

CalendarOps bridges the gap between raw calendar data and personal lifestyle goals (gym, school, coding). The system uses a LangGraph agent to orchestrate an LLM that reasons about scheduling conflicts and manages time slots. A React frontend gives it a chat interface, and a FastAPI backend handles the Google OAuth flow and agent execution.

The core design principle is human-in-the-loop: the agent can suggest and create events, but it surfaces what it is doing before completing any write operation.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| Agent Orchestration | LangGraph |
| LLM | Hugging Face Inference API (default: `meta-llama/Llama-3.3-70B-Instruct`) |
| Backend API | FastAPI + Uvicorn |
| Frontend | React 19 + Vite |
| Calendar Integration | Google Calendar API (OAuth 2.0) |
| Environment | python-dotenv |

---

## Project Structure

```
CalendarAgent/
├── .env                        # API keys and model config (not committed)
├── .gitignore
├── requirements.txt
├── README.md
├── backend/
│   ├── main.py                 # FastAPI app — routes, OAuth flow, /chat endpoint
│   ├── agent.py                # LangGraph graph definition and run_agent()
│   └── src/
│       ├── auth.py             # Google OAuth helper (get_calendar_service)
│       ├── llm.py              # HuggingFace LLM initialization
│       ├── state.py            # LangGraph TypedDict state schema
│       ├── credentials.json    # Google OAuth client secret (not committed)
│       ├── token.json          # Generated after first login (not committed)
│       └── tools/
│           └── gcal.py         # get_calendar_events() and create_event() tools
└── frontend/
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── App.jsx             # Main chat UI component
        ├── main.jsx
        └── index.css
```

---

## Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- A Google Cloud project with the Calendar API enabled
- A Hugging Face account with an API token

---

## Setup

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd CalendarAgent
```

### 2. Set up the Python virtual environment

```bash
python -m venv Calendar
```

Activate it:

- Windows: `Calendar\Scripts\Activate`
- macOS/Linux: `source Calendar/bin/activate`

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
HUGGINGFACEHUB_API_TOKEN=hf_your_token_here

# The default model is Qwen/Qwen2.5-7B-Instruct.
# Larger models have significantly better tool-calling reliability:
HF_MODEL=meta-llama/Llama-3.3-70B-Instruct
# HF_MODEL=Qwen/Qwen2.5-72B-Instruct
```

Your Hugging Face token needs Inference API access. Get one at https://huggingface.co/settings/tokens.

### 5. Set up Google Calendar credentials

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use an existing one)
3. Enable the **Google Calendar API**
4. Go to "APIs & Services" > "Credentials" > "Create Credentials" > "OAuth 2.0 Client ID"
5. Set the application type to **Web application**
6. Add `http://localhost:8000/auth/callback` as an authorized redirect URI
7. Download the JSON file and save it to `backend/src/credentials.json`

### 6. Install frontend dependencies

```bash
cd frontend
npm install
```

---

## Running the App

You need two terminals running simultaneously, or use the combined start script.

**Option A: Combined start (from the `frontend` directory)**

```bash
cd frontend
npm start
```

This uses `concurrently` to start both the backend and frontend together.

**Option B: Two separate terminals**

Terminal 1 — start the backend:
```bash
cd backend
uvicorn main:app --reload
```

Terminal 2 — start the frontend:
```bash
cd frontend
npm run dev
```

Once both are running:

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

On first launch, click "Connect Google Calendar" in the UI. You'll be redirected to Google's OAuth consent screen. After approving, you'll be sent back to the app and the agent will be ready to use.

The OAuth token is saved to `backend/src/token.json` and reused on subsequent runs. You won't need to re-authenticate unless the token expires or you disconnect.

---

## How It Works

The agent follows a standard ReAct loop, implemented as a LangGraph state machine:

```
User message
    |
    v
[agent node]  ->  LLM decides: answer directly OR call a tool
    |
    | (tool call)
    v
[action node] ->  Executes get_calendar_events() or create_event()
    |
    v
[agent node]  ->  LLM sees the tool result and generates a final response
    |
    v
Response returned to frontend via /chat endpoint
```

State is persisted in-memory using LangGraph's `MemorySaver`, keyed by `thread_id`. Within a session, the agent remembers the conversation history.

The backend exposes four main routes:

| Route | Purpose |
|---|---|
| `GET /auth/login` | Redirects to Google OAuth consent |
| `GET /auth/callback` | Handles OAuth redirect, saves token |
| `GET /auth/status` | Checks if a valid token exists |
| `POST /chat` | Sends a message to the agent |

---

## Agent Rules

These are enforced via the system prompt and are not configurable at runtime:

- The agent always calls `get_calendar_events` before answering any question about your schedule. It never answers from memory.
- The agent always calls `create_event` before saying it has added something. It does not confirm an action it has not taken.
- Relative time references ("tomorrow", "next Monday") are resolved to exact dates based on the current date injected into the system prompt.
- All times default to `America/Los_Angeles` unless you specify otherwise.
- Every transition between activities (school to gym, gym to work) requires a 15-minute buffer.
- Priority order: School > Pre-planned events > Gym > Coding projects.

---

## Implementation Phases

- Phase 1 — Google OAuth 2.0 handshake and Calendar CRUD tooling
- Phase 2 — LangGraph state schema and agent graph design
- Phase 3 — LLM integration via Hugging Face Inference API
- Phase 4 — "Gym Window" reasoning logic (scheduling around soft constraints)
- Phase 5 — Gmail API integration (planned)