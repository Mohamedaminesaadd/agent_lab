from typing import Annotated, TypedDict

from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI


class GraphState(TypedDict):
    messages: Annotated[list, add_messages]


# ---------------- Tools ---------------- #

@tool
def add(a: int, b: int):
    """Add two numbers."""
    return a + b


@tool
def multiply(a: int, b: int):
    """Multiply two numbers."""
    return a * b


tools = [add, multiply]

# ---------------- LLM ---------------- #

llm = ChatOpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
    model="qwen2.5:14b",
)

llm = llm.bind_tools(tools)

# ---------------- Nodes ---------------- #

def chatbot(state: GraphState):
    response = llm.invoke(state["messages"])

    print(response)
    print(response.tool_calls)
    print(response.invalid_tool_calls)

    return {"messages": [response]}


tool_node = ToolNode(tools)

# ---------------- Graph ---------------- #

graph = StateGraph(GraphState)

graph.add_node("chatbot", chatbot)
graph.add_node("tools", tool_node)

graph.add_edge(START, "chatbot")

graph.add_conditional_edges(
    "chatbot",
    tools_condition,
)

graph.add_edge("tools", "chatbot")

app = graph.compile()





### teste 
from langchain_core.messages import HumanMessage

result = app.invoke({
    "messages": [
        HumanMessage(content="What is 12 * 7?")
    ]
})

for msg in result["messages"]:
    print(msg)