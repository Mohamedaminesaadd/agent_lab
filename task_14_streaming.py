from typing import TypedDict
from langgraph.graph import StateGraph, START, END

# =====================================================
# State
# =====================================================

class GraphState(TypedDict):
    message: str
    number :int


# =====================================================
# Nodes
# =====================================================

def greeting_node(state: GraphState):

    print("Greeting Node")

    return {
        "message": "Hello Mohamed"
    }


def uppercase_node(state: GraphState):

    print("Uppercase Node")

    return {
        "message": state["message"].upper()
    }



# =====================================================
# Build Graph
# =====================================================

builder = StateGraph(GraphState)

builder.add_node("greeting", greeting_node)
builder.add_node("uppercase", uppercase_node)

builder.add_edge(START, "greeting")
builder.add_edge("greeting", "uppercase")
builder.add_edge("uppercase", END)

graph = builder.compile()

initial_state = {
    "message": "hello from lab 14",
    "int":14
}

print("\n========== STREAM ==========\n")

for event in graph.stream(
    initial_state,
    stream_mode="values"
):
    print(event)