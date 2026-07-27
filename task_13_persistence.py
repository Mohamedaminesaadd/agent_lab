from typing import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver


# =====================================================
# State
# =====================================================

class GraphState(TypedDict):
    name: str
    greeting: str


# =====================================================
# Node
# =====================================================

def greeting_node(state: GraphState):

    print("Greeting Node")

    return {
        "greeting": f"Hello {state['name']}!"
    }


# =====================================================
# Graph
# =====================================================

builder = StateGraph(GraphState)

builder.add_node(
    "greeting",
    greeting_node,
)

builder.add_edge(
    START,
    "greeting",
)

builder.add_edge(
    "greeting",
    END,
)


# =====================================================
# SQLite Checkpointer
# =====================================================




# =====================================================
# Run
# =====================================================
with SqliteSaver.from_conn_string("graph.db") as sqlite:

    graph = builder.compile(checkpointer=sqlite)

    config = {
        "configurable": {
            "thread_id": "user_1"
        }
    }
    state = graph.get_state(config)
    print(state)
    
"""
    result = graph.invoke(
        {"name": "Mohamed"},
        config=config
    )

    print(result)
"""
    