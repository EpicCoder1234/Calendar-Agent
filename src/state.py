from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # The 'messages' key holds the entire chat history.
    # 'add_messages' is a "reducer" — it tells LangGraph: 
    # "Don't overwrite this list, just append new messages to the end."

    # Start your state with this message + the user message
    messages: Annotated[list, add_messages]
    
    # You can add more keys here later, like:
    # user_location: str
    # current_priority: int