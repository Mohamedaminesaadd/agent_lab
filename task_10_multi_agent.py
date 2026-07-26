"""
==========================================================
LANGGRAPH MULTI-AGENT SYSTEM
==========================================================

Sections
1. Imports
2. Graph State
3. Tools
4. LLM Configuration
5. Prompts
6. Tool Binding
7. Agents
8. Supervisor
9. Tool Nodes
10. Graph Construction
11. Execution
==========================================================
"""

# ==========================================================
# 1. IMPORTS
# ==========================================================

from pprint import pprint
from typing import Annotated, TypedDict

from langchain_core.messages import SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition


# ==========================================================
# 2. GRAPH STATE
# ==========================================================

class GraphState(TypedDict):

    messages: Annotated[list, add_messages]

    next_agent: str

    hotel: str

    flight_reserved: bool

    vacation_requested: bool


# ==========================================================
# 3. TOOLS
# ==========================================================

HOTELS = {
    "Tunisia": [
        "Golden Tulip",
        "Movenpick Sousse",
        "Iberostar Selection",
    ],
    "Spain": [
        "Hotel Ritz Madrid",
        "Barcelona Princess",
        "Gran Hotel Bali",
    ],
    "France": [
        "Le Meurice",
        "Hotel Lutetia",
        "Shangri-La Paris",
    ],
}


@tool
def search_hotel(country: str) -> str:
    """Search hotels."""

    hotels = HOTELS.get(country)

    if hotels is None:
        return f"No hotels found in {country}."

    return "\n".join(hotels)


@tool
def reserve_airplane(destination: str) -> str:
    """Reserve an airplane ticket."""

    return f"Flight to {destination} reserved successfully."


@tool
def take_vacation(days: int) -> str:
    """Notify HR."""

    return f"Vacation for {days} days approved."


hotel_tools = [search_hotel]
flight_tools = [reserve_airplane]
hr_tools = [take_vacation]


# ==========================================================
# 4. LLM CONFIGURATION
# ==========================================================

base_llm = ChatOpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
    model="qwen2.5:14b",
    temperature=0,
)

hotel_llm = base_llm.bind_tools(hotel_tools)
flight_llm = base_llm.bind_tools(flight_tools)
hr_llm = base_llm.bind_tools(hr_tools)


# ==========================================================
# 5. PROMPTS
# ==========================================================

HOTEL_PROMPT = SystemMessage(
    content="""
You are the Hotel Specialist.

Responsibilities:
- Search hotels.
- Recommend hotels.

Always call the search_hotel tool.

Never reserve flights.
Never notify HR.
"""
)

FLIGHT_PROMPT = SystemMessage(
    content="""
You are the Flight Specialist.

Responsibilities:
- Reserve airplane tickets.

Always call reserve_airplane.

Never search hotels.
Never notify HR.
"""
)

HR_PROMPT = SystemMessage(
    content="""
You are the HR Specialist.

Responsibilities:
- Notify HR about vacations.

Always call take_vacation.

Never reserve flights.
Never search hotels.
"""
)


# ==========================================================
# 6. AGENTS
# ==========================================================

def hotel_agent(state: GraphState):

    print("\n========== HOTEL AGENT ==========")
    pprint(state)

    last_message = state["messages"][-1]

    if isinstance(last_message, ToolMessage):

        selected_hotel = last_message.content.split("\n")[0]

        print("Selected Hotel:", selected_hotel)

        return {
            "hotel": selected_hotel
        }

    response = hotel_llm.invoke(
        [
            HOTEL_PROMPT,
            *state["messages"],
        ]
    )

    print(response.tool_calls)

    return {
        "messages": [response]
    }


def flight_agent(state: GraphState):

    print("\n========== FLIGHT AGENT ==========")
    pprint(state)

    last_message = state["messages"][-1]

    if isinstance(last_message, ToolMessage):

        print("Flight Reserved")

        return {
            "flight_reserved": True
        }

    response = flight_llm.invoke(
        [
            FLIGHT_PROMPT,
            *state["messages"],
        ]
    )

    print(response.tool_calls)

    return {
        "messages": [response]
    }


def hr_agent(state: GraphState):

    print("\n========== HR AGENT ==========")
    pprint(state)

    last_message = state["messages"][-1]

    if isinstance(last_message, ToolMessage):

        print("HR Notified")

        return {
            "vacation_requested": True
        }

    response = hr_llm.invoke(
        [
            HR_PROMPT,
            *state["messages"],
        ]
    )

    print(response.tool_calls)

    return {
        "messages": [response]
    }


# ==========================================================
# 7. SUPERVISOR
# ==========================================================

def supervisor(state: GraphState):

    print("\n========== SUPERVISOR ==========")
    pprint(state)

    if state["hotel"] == "":
        decision = "hotel"

    elif not state["flight_reserved"]:
        decision = "flight"

    elif not state["vacation_requested"]:
        decision = "hr"

    else:
        decision = "finish"

    print("Decision:", decision)

    return {
        "next_agent": decision
    }


def supervisor_router(state: GraphState):
    return state["next_agent"]


# ==========================================================
# 8. TOOL NODES
# ==========================================================

hotel_tool_node = ToolNode(hotel_tools)
flight_tool_node = ToolNode(flight_tools)
hr_tool_node = ToolNode(hr_tools)


# ==========================================================
# 9. BUILD GRAPH
# ==========================================================

graph = StateGraph(GraphState)

graph.add_node("supervisor", supervisor)

graph.add_node("hotel_agent", hotel_agent)
graph.add_node("hotel_tools", hotel_tool_node)

graph.add_node("flight_agent", flight_agent)
graph.add_node("flight_tools", flight_tool_node)

graph.add_node("hr_agent", hr_agent)
graph.add_node("hr_tools", hr_tool_node)

graph.add_edge(START, "supervisor")

graph.add_conditional_edges(
    "supervisor",
    supervisor_router,
    {
        "hotel": "hotel_agent",
        "flight": "flight_agent",
        "hr": "hr_agent",
        "finish": END,
    },
)

graph.add_conditional_edges(
    "hotel_agent",
    tools_condition,
    {
        "tools": "hotel_tools",
        END: "supervisor",
    },
)

graph.add_edge("hotel_tools", "hotel_agent")

graph.add_conditional_edges(
    "flight_agent",
    tools_condition,
    {
        "tools": "flight_tools",
        END: "supervisor",
    },
)

graph.add_edge("flight_tools", "flight_agent")

graph.add_conditional_edges(
    "hr_agent",
    tools_condition,
    {
        "tools": "hr_tools",
        END: "supervisor",
    },
)

graph.add_edge("hr_tools", "hr_agent")

app = graph.compile(debug = True)


# ==========================================================
# 10. RUN
# ==========================================================

if __name__ == "__main__":

    initial_state = {

        "messages": [
            (
                "user",
                "I want to travel to Spain. "
                "Find me a hotel, reserve my flight "
                "and notify HR that I will be on vacation for 7 days."
            )
        ],

        "next_agent": "",

        "hotel": "",

        "flight_reserved": False,

        "vacation_requested": False,
    }

    result = app.invoke(initial_state)

    print("\n========== FINAL STATE ==========")
    pprint(result)

    print("\n========== FINAL CONVERSATION ==========")

    for message in result["messages"]:
        message.pretty_print()