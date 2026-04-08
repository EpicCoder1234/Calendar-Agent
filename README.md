# Life-Ops: Agentic Personal Scheduler

## 🎯 Project Objective
To build an autonomous, multi-agent system that bridges the gap between raw calendar data and personal lifestyle goals (Gym, School, Coding). The system uses LLMs to reason about scheduling conflicts and autonomously manage time-slots with a "Human-in-the-Loop" safety gate.

## 🛠 Tech Stack
- **Language:** Python 3.11+
- **Orchestration:** LangGraph (for state-machine control)
- **Intelligence:** Hugging Face Inference API (Model: `meta-llama/Llama-3-70B-Instruct` or `mistralai/Mixtral-8x7B-v0.1`)
- **Tools:** Google Calendar API, Gmail API
- **Environment:** Docker (for future deployment), Python-dotenv

# 🧬 Life-Ops: Agentic Personal Scheduler

## 1. Project Overview
An autonomous scheduling system that leverages **Multi-Agent Orchestration** to bridge the gap between high-level lifestyle goals (Gym, Research, Coding) and raw calendar data. It uses open-source LLMs to reason about "soft" constraints like travel buffers and priorities.

## 2. Workspace & File Structure
```text
life-ops-agent/
├── .env                # Secret Keys (HF_TOKEN, GOOGLE_CLIENT_ID)
├── .gitignore          # Ignore venv/, .env, token.json
├── README.md           # This Design Document
├── requirements.txt    # dependencies
├── data/
│   ├── credentials.json # OAuth Secret from Google Console
│   └── token.json       # Generated after first login
└── src/
    ├── main.py          # Entry point & CLI loop
    ├── state.py         # TypedDict defining the Graph State
    ├── nodes.py         # Node functions (LLM logic + Tool calls)
    └── tools/           # API wrappers
        ├── calendar_tools.py
        └── gmail_tools.py
```
## 🏗 System Architecture
The system operates as a Directed Acyclic Graph (DAG) with the following nodes:
1. **The Ingestor:** Authenticates and pulls raw events from Google Calendar.
2. **The Logic Agent:** An LLM that maps "Natural Language" (e.g., "after school") to specific timestamps based on your schedule.
3. **The Conflict Resolver:** Checks if a proposed action (e.g., "Gym at 4 PM") overlaps with existing events.
4. **The Executor:** Prepares the final API call to update the calendar.

## 📜 Agent Rules (The "Business Logic")
- **The 15-Minute Rule:** Every transition (e.g., School -> Gym) must include a 15-minute buffer.
- **Priority Hierarchy:** School > Pre-planned Events > Gym > Coding Projects.
- **Human-in-the-Loop:** The agent can *suggest* a change, but it cannot write to the Google Calendar API without an explicit `[APPROVE]` command in the terminal.
- **Timezone Integrity:** All operations must default to `America/Los_Angeles`.

## 🚀 Implementation Phases
- **Phase 1:** OAuth 2.0 Handshake & Calendar CRUD Tooling.
- **Phase 2:** Designing the LangGraph State and Schema.
- **Phase 3:** LLM Integration via Hugging Face.
- **Phase 4:** Developing the "Gym Window" reasoning logic.