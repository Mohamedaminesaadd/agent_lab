from typing import Annotated, TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage


# =====================================================
# STATE
# =====================================================

class GraphState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


# =====================================================
# NODE
# =====================================================

def chatbot(state: GraphState):

    last_message = state["messages"][-1]

    response = AIMessage(
        content=f"You said: {last_message.content}"
    )

    return {
        "messages": [response]
    }


# =====================================================
# GRAPH
# =====================================================

graph = StateGraph(GraphState)

graph.add_node("chatbot", chatbot)

graph.add_edge(START, "chatbot")
graph.add_edge("chatbot", END)


# =====================================================
# MEMORY
# =====================================================

memory = InMemorySaver()

app = graph.compile(
    checkpointer=memory
)


# =====================================================
# CONFIG
# =====================================================

config = {
    "configurable": {
        "thread_id": "conversation_1"
    }
}


# =====================================================
# FIRST INVOCATION
# =====================================================

app.invoke(
    {
        "messages": [
            HumanMessage(content="Hello")
        ]
    },
    config=config
)


# =====================================================
# READ MEMORY
# =====================================================

state = app.get_state(config)

print("Conversation history:\n")

for message in state.values["messages"]:
    print(f"{message.type}: {message.content}")