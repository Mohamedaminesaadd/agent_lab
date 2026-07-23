from random import randint
from typing import TypedDict
from langgraph.graph import StateGraph, START, END


class GraphState(TypedDict):
    number1: int
    number2: int
    loopNumber: int


def node_rand(state: GraphState):
    rn1 = randint(0, 10)
    rn2 = randint(0, 10)

    print(f"Generated: {rn1} - {rn2}")

    return {
        "number1": rn1,
        "number2": rn2,
        "loopNumber": state["loopNumber"] + 1,
    }


def node_valid(state: GraphState):
    print("Numbers are equal!")
    print(f"Found after {state['loopNumber']} attempts.")
    return {}


def router(state: GraphState):
    if state["number1"] == state["number2"]:
        return "valid"

    return "retry"


graph = StateGraph(GraphState)

graph.add_node("node_rand", node_rand)
graph.add_node("node_valid", node_valid)

graph.add_edge(START, "node_rand")

graph.add_conditional_edges(
    "node_rand",
    router,
    {
        "retry": "node_rand",      # boucle
        "valid": "node_valid",
    },
)

graph.add_edge("node_valid", END)

app = graph.compile()

result = app.invoke(
    {
        "number1": 0,
        "number2": 0,
        "loopNumber": 0,
    }
)

print(result)