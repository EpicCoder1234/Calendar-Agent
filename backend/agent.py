import os
from datetime import date
from dotenv import load_dotenv

# Load .env from the project root (one level up from backend/)
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

from src.state import AgentState
from src.llm import get_llm
from src.tools.gcal import get_calendar_events, create_event

# ── Build the graph once at startup ──────────────────────────────────────────

_llm = get_llm()
_tools = [get_calendar_events, create_event]
_llm_with_tools = _llm.bind_tools(_tools)


def _call_model(state: AgentState):
    messages = state["messages"]
    response = _llm_with_tools.invoke(messages)
    return {"messages": [response]}


_workflow = StateGraph(AgentState)
_workflow.add_node("agent", _call_model)
_workflow.add_node("action", ToolNode(_tools))
_workflow.set_entry_point("agent")
_workflow.add_conditional_edges(
    "agent",
    tools_condition,
    {"tools": "action", END: END}
)
_workflow.add_edge("action", "agent")

_memory = MemorySaver()
_app = _workflow.compile(checkpointer=_memory)

# ── System prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT_TEMPLATE = """You are Life-Ops, a smart personal scheduling assistant with direct access to the user's Google Calendar.

Today's date is {today}.

RULES YOU MUST FOLLOW — NO EXCEPTIONS:
1. ALWAYS call `get_calendar_events` BEFORE answering ANY question about the user's schedule, free time, upcoming events, or availability. Never guess or answer from memory.
2. ALWAYS call `create_event` to add anything to the calendar. Never say "I've added it" or "Done!" without actually invoking the tool first.
3. When the user uses relative time references like "tomorrow", "next Monday", or "this weekend", calculate the exact date from today's date above before calling any tools.
4. After receiving tool output, summarize the results clearly and concisely. Do not dump raw data.
5. All times default to America/Los_Angeles timezone unless the user specifies otherwise.
6. If a request is ambiguous (e.g. no end time given), make a reasonable assumption and state it clearly.
"""


# ── Public API ────────────────────────────────────────────────────────────────

def run_agent(message: str, thread_id: str = "default") -> dict:
    """
    Run the LangGraph agent with a user message.
    Returns a dict with 'response' (str) and 'tool_calls' (list of tool names used).
    """
    config = {"configurable": {"thread_id": thread_id}}
    today_str = date.today().strftime("%A, %B %d, %Y")
    system_msg = SystemMessage(content=SYSTEM_PROMPT_TEMPLATE.format(today=today_str))

    inputs = {"messages": [system_msg, HumanMessage(content=message)]}

    response_text = ""
    tool_calls_made = []

    for output in _app.stream(inputs, config=config):
        for key, value in output.items():
            last_msg = value["messages"][-1]
            if key == "agent" and last_msg.content:
                response_text = last_msg.content
            if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                tool_calls_made = [tc["name"] for tc in last_msg.tool_calls]

    return {
        "response": response_text,
        "tool_calls": tool_calls_made,
    }
