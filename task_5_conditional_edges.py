from random import randint, random
from typing import TypedDict
from langgraph.graph import StateGraph, START, END


class GraphState(TypedDict):
    number:int
    path:str

def node_rand(state:GraphState):
    print("Node generate number")
    rn = randint(0,100)
    return {"number": rn}


def node_path1(state:GraphState):
    print("the number is over 50")
    return{
    "path":"the path is through the node path1"
}


def node_path2(state:GraphState):
    print("the number is under 50")
    return{
    "path":"the path is through the node path2"
}

graph = StateGraph(GraphState)

graph.add_node("node_rand", node_rand)
graph.add_node("node_path1", node_path1)
graph.add_node("node_path2", node_path2)


graph.add_edge(START, "node_rand")

#On ne peut pas accéder au state en dehors d'un node

# if faur creer une fonction de routage


def router(state: GraphState):
    if state["number"] >= 50:
        return "node_path1"
    else:
        return "node_path2"

# Utiliser add_conditional_edges

graph.add_conditional_edges(
    "node_rand",
    router,
    {
        "node_path1": "node_path1",
        "node_path2": "node_path2",
    },
)

graph.add_edge("node_path1", END)
graph.add_edge("node_path2", END)

app = graph.compile()


#invoke() doit recevoir un état initial

result = app.invoke(
    {
        "number": 0,
        "path": ""
    }
)
print(result)
