from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from langgraph.prebuilt import create_react_agent

@tool
def add(a: int, b: int):
    """Add two numbers."""
    return a + b


@tool
def multiply(a: int, b: int):
    """Multiply two numbers."""
    return a * b

llm = ChatOpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
    model="qwen2.5:14b",
)


agent = create_react_agent(
    model=llm,
    tools=[add, multiply]
)


#invoke 
from langchain_core.messages import HumanMessage

result = agent.invoke(
    {
        "messages": [
            HumanMessage(
                content="What is (15 * 8) + 10 ?"
            )
        ]
    }
)

for message in result["messages"]:
    print(message)

#it's not use for the complex workflow 
# so build the the idea of thr task 8 full control vs quick step 