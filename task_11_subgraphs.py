from typing import Annotated, TypedDict
from pprint import pprint

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI


# ==========================================================
# State
# ==========================================================

class GraphState(TypedDict):
    messages: Annotated[list, add_messages]
    hotel: str


# ==========================================================
# Hotels
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


# ==========================================================
# Tool
# ==========================================================

@tool
def search_hotel(country: str) -> str:
    """Search hotels by country."""

    hotels = HOTELS.get(country)

    if hotels is None:
        return f"No hotels found in {country}."

    return "\n".join(hotels)


def update_hotel_state(state: GraphState):

    last_message = state["messages"][-1]

    if isinstance(last_message, ToolMessage):
        data = json.loads(last_message.content)

        return {
            "hotel": data["hotel"]
        }

    return {}

# ==========================================================
# LLM
# ==========================================================

llm = ChatOpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
    model="qwen2.5:14b",
    temperature=0,
)

hotel_llm = llm.bind_tools([search_hotel])


# ==========================================================
# Prompt
# ==========================================================

HOTEL_PROMPT = SystemMessage(
    content="""
You are a hotel assistant.

If the user asks for a hotel in a country,
ALWAYS use the search_hotel tool.

Never answer from memory.
"""
)


# ==========================================================
# Agent
# ==========================================================

def hotel_agent(state: GraphState):

    print("\n========== HOTEL AGENT ==========")
    pprint(state)

    response = hotel_llm.invoke(
        [
            HOTEL_PROMPT,
            *state["messages"],
        ]
    )

    print("\nLLM Response")
    print(response)

    print("\nTool Calls")
    print(response.tool_calls)

    return {
        "messages": [response]
    }


# ==========================================================
# Tool Node
# ==========================================================

tool_node = ToolNode([search_hotel])


# ==========================================================
# Graph
# ==========================================================

graph = StateGraph(GraphState)

graph.add_node("hotel_agent", hotel_agent)
graph.add_node("tools", tool_node)

graph.add_edge(START, "hotel_agent")

graph.add_conditional_edges(
    "hotel_agent",
    tools_condition,
    {
        "tools": "tools",
        END: END,
    },
)

graph.add_edge("tools", "hotel_agent")

app = graph.compile()


# ==========================================================
# Run
# ==========================================================

if __name__ == "__main__":

    result = app.invoke(
        {
            "messages": [
                (
                    "user",
                    "Find me a hotel in Spain."
                )
            ]
        }
    )

    print("\n========== FINAL ==========\n")

    for message in result["messages"]:
        message.pretty_print()