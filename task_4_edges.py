from typing import TypedDict
from langgraph.graph import StateGraph, START, END


class GraphState(TypedDict):
    message: str



def node_a(state: GraphState):

    print("Node A")

    return {
        "message": state["message"] + " -> A"
    }


def node_b(state: GraphState):

    print("Node B")

    return {
        "message": state["message"] + " -> B"
    }


def node_c(state: GraphState):

    print("Node C")

    return {
        "message": state["message"] + " -> C"
    }


graph = StateGraph(GraphState)

graph.add_node("node_a", node_a)
graph.add_node("node_b", node_b)
graph.add_node("node_c", node_c)


graph.add_edge(START, "node_a")

graph.add_edge("node_a", "node_b")

graph.add_edge("node_b", "node_c")

graph.add_edge("node_c", END)


app = graph.compile()

result = app.invoke(
    {
        "message": "Start"
    }
)

print(result)