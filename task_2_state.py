from typing import TypedDict
from langgraph.graph import StateGraph,START,END

# ==========================
# State Definition
# ==========================
class GrapheState(TypedDict):
    name:str
    age:int
    city:str
    greeting:str


# ==========================
# Nodes
# ==========================

def greeting_node(state:GrapheState):
    """create a greeting using the user's name and city"""
    print("\n--- Greeting Node ---")
    print("recivesd state:",state)
    greeting = f"hello {state['name']} from {state['city']}!"
    return {
        "greeting":greeting
    }

def age_node(state:GrapheState):
    """append adult or minor to the greeting"""

    print("\n--age nde--")
    print("recevied state:",state)

    if state["age"] >=18:
        status = "adult"
    else:
        status = "minor"

    return {
        "greeting" :state["greeting"] + f"{status}"
    }

def final_node(state:GrapheState):
    """display the finale state"""

    print("\n---finale node---")
    print("received state",state)

    return state


#==========================
# Build Graph
# ==========================
graph = StateGraph(GrapheState)

graph.add_node("greeting", greeting_node)
graph.add_node("age", age_node)
graph.add_node("final", final_node)

# lie the nodes with the edges 
graph.add_edge(START, "greeting")
graph.add_edge("greeting", "age")
graph.add_edge("age", "final")
graph.add_edge("final", END)

app = graph.compile()



# ==========================
# Execute
# ==========================

initial_state = {
    "name": "Mohamed",
    "age": 22,
    "city": "Sfax",
    "greeting": ""
}


result = app.invoke(initial_state)

print("\n=========================")
print("Returned Result")
print("=========================")
print(result)



"""
    A node should:
        Read what it needs from the state.
        Compute its result.
        Return only the fields it wants to update.

        This is the standard pattern you'll 
        use in almost every LangGraph application.
"""