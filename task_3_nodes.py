from typing import TypedDict
from langgraph.graph import StateGraph, START, END


class GraphState(TypedDict):
    name: str
    age: int
    greeting: str
    category: str

def greeting_node(state: GraphState):

    print("Greeting Node")

    return {
        "greeting": f"Hello {state['name']}!"
    }


def age_node(state: GraphState):

    print("Age Node")

    category = "Adult" if state["age"] >= 18 else "Minor"

    return {
        "category": category
    }


def final_node(state: GraphState):

    print("Final Node")

    message = (
        f"{state['greeting']} "
        f"You are an {state['category']}."
    )

    print(message)

    return {}



graph = StateGraph(GraphState)

graph.add_node("greeting", greeting_node)
graph.add_node("age", age_node)
graph.add_node("final", final_node)

graph.add_edge(START, "greeting")
graph.add_edge("greeting", "age")
graph.add_edge("age", "final")
graph.add_edge("final", END)

app = graph.compile()


result = app.invoke(
    {
        "name": "Mohamed",
        "age": 22,
        "greeting": "",
        "category": ""
    }
)

print(result)