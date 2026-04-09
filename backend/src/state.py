from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    
    # You can add more keys here later, like:
    # user_location: str
    # current_priority: int