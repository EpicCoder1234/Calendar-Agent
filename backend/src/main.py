import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from langgraph.prebuilt import ToolNode
from state import AgentState
from llm import get_llm
from auth import get_calendar_service
from tools.gcal import get_calendar_events, create_event


# Create the tools 


llm = get_llm()
tools = [get_calendar_events, create_event]
llm_with_tools = llm.bind_tools(tools)
def call_model(state: AgentState):
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

action_node = ToolNode(tools)




# STEP 1: USER INPUT

# STEP 2: LLM NODE
# The LLM looks at state["messages"]
# It thinks: "I need to see the calendar."
# It returns an AIMessage with reasoning and a tool call.
# LangGraph APPENDS this to the state.

# STEP 3: TOOL NODE
# The Tool Node sees the tool call in the latest message.
# It runs your Python function: get_calendar_events().
# It creates a ToolMessage with the calendar data.
# LangGraph APPENDS this to the state.

# STEP 4: BACK TO LLM
# The LLM now sees the whole history on the 'clipboard' (the State).
# It sees its own thought + the calendar data.
# It finally says: "You are free at 4 PM!"


from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode, tools_condition
from state import AgentState
from tools.gcal import get_calendar_events, create_event

workflow = StateGraph(AgentState)

workflow.add_node("agent", call_model)
workflow.add_node("action", ToolNode([get_calendar_events, create_event]))

workflow.set_entry_point("agent")

workflow.add_conditional_edges(
    "agent",
    tools_condition,
    {"tools": "action", END: END}
)

workflow.add_edge("action", "agent")

app = workflow.compile()

system_msg = {
    "role": "system", 
    "content": "You are a Life-Ops executive assistant. You have access to Google Calendar. "
               "When you receive tool output, summarize it clearly for the user. "
               "Always reference the current date to determine what 'tomorrow' means."
    }   

from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

if __name__ == "__main__":

    config = {"configurable": {"thread_id": "hruday_test_session"}}
    
    print("--- 🚀 Life-Ops Chat Active (type 'quit' to exit) ---")
    
    while True:
        user_input = input("\nUser: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            break

        inputs = {"messages": [system_msg, HumanMessage(content=user_input)]}

        for output in app.stream(inputs, config=config):
            for key, value in output.items():
                last_msg = value["messages"][-1]
                if key == "agent" and last_msg.content:
                    print(f"\nAgent: {last_msg.content}")
                if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                    print(f"  [System: Searching {last_msg.tool_calls[0]['name']}...]")