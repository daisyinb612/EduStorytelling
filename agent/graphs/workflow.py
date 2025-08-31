from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, AIMessage

from agents.human_agent import dialogue_node
from agents.model_agent import ModelAgent

class AgentState(TypedDict):
    """定义图工作流的状态"""
    messages: Annotated[list, add_messages]
    # 从 dialogue_node 传递格式化后的提示到 model_node
    messages_to_model: List[BaseMessage]

def create_chat_workflow(model_agent: ModelAgent):
    """创建一个基本的交互式对话工作流"""

    def model_node(state: AgentState) -> dict:
        """调用模型获取回答"""
        print("---模型正在生成回答...---")
        prompt = state.get("messages_to_model")
        response_content = model_agent.respond(prompt)
        # 将AI的回答添加到消息历史中
        return {"messages": [AIMessage(content=response_content)]}

    # 定义图
    builder = StateGraph(AgentState)
    builder.add_node("dialogue", dialogue_node)
    builder.add_node("model", model_node)

    # 定义边：从对话节点到模型节点，然后结束
    builder.set_entry_point("dialogue")
    builder.add_edge("dialogue", "model")
    builder.add_edge("model", END)

    return builder.compile()