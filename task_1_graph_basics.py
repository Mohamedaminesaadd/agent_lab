from langgraph.graph import StateGraph, START, END
from typing import TypedDict

class GraphState(TypedDict):
    message:str

#create nodes 

# 1 greeting node
def greeting_node(state: GraphState):
    print("Greeting Node")
    return {"message": state["message"] + " 👋"}

# 2 upercase node 
def uppercase_node(state: GraphState):
    print("uppercase node")
    return {"message":state["message"].upper()}

#finale node 
def final_node(state: GraphState):
    print("finale node")
    print("finale message: ",state["message"])



#buide the graphe 
graph = StateGraph(GraphState)

# add noued 
graph.add_node("greeting",greeting_node)
graph.add_node("uppercase_node",uppercase_node)
graph.add_node("finale_node",final_node)

#connect this nodes
graph.add_edge(START,"greeting")
graph.add_edge("greeting","uppercase_node")
graph.add_edge("uppercase_node","finale_node")
graph.add_edge("finale_node",END)

#Compile
app = graph.compile()

#run the graph 
result = app.invoke(
    {
        "message":"hello LangGraph"
    }
)

print(result)