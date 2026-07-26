from typing import TypedDict

from langgraph.graph import StateGraph, START, END


# ==========================================================
# State
# ==========================================================

class TravelState(TypedDict):
    destination: str
    hotel: str
    flight_reserved: bool


# ==========================================================
# Nodes
# ==========================================================

def hotel_node(state: TravelState):

    print("\n========== HOTEL NODE ==========")

    destination = state["destination"]

    return {
        "hotel": f"Hotel booked in {destination}"
    }


def flight_node(state: TravelState):

    print("\n========== FLIGHT NODE ==========")

    return {
        "flight_reserved": True
    }


# ==========================================================
# Build Subgraph
# ==========================================================

travel_builder = StateGraph(TravelState)

travel_builder.add_node("hotel", hotel_node)
travel_builder.add_node("flight", flight_node)

travel_builder.add_edge(START, "hotel")
travel_builder.add_edge("hotel", "flight")
travel_builder.add_edge("flight", END)


# ==========================================================
# Compile
# ==========================================================

travel_graph = travel_builder.compile()


# ==========================================================
# Test
# ==========================================================

if __name__ == "__main__":

    initial_state = {
        "destination": "Spain",
        "hotel": "",
        "flight_reserved": False,
    }

    result = travel_graph.invoke(initial_state)

    print("\n========== FINAL STATE ==========\n")

    print(result)




#parnet state 
class MainState(TypedDict):
    destination: str
    hotel: str
    flight_reserved: bool

#Notice that it contains the same fields required by the travel_graph.

def supervisor_node(state: MainState):

    print("\n========== SUPERVISOR ==========")

    print("Starting the travel workflow...")

    return {}

main_builder = StateGraph(MainState)



#The key idea is that a compiled graph can be added as a node.
main_builder.add_node(
    "supervisor",
    supervisor_node,
)

main_builder.add_node(
    "travel",
    travel_graph,
)


main_builder.add_edge(
    START,
    "supervisor",
)

main_builder.add_edge(
    "supervisor",
    "travel",
)

main_builder.add_edge(
    "travel",
    END,
)

main_graph = main_builder.compile()

if __name__ == "__main__":

    initial_state = {
        "destination": "Spain",
        "hotel": "",
        "flight_reserved": False,
    }

    result = main_graph.invoke(initial_state)

    print("\n========== FINAL STATE ==========\n")

    print(result)