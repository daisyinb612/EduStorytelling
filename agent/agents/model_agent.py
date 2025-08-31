import os
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import SystemMessage

class ModelAgent:
    def __init__(self, model_name="deepseek-chat"):
        api_key = os.environ.get("DEEPSEEK_API_KEY2")
        self.deepseek = ChatDeepSeek(
            model=model_name,
            temperature=0,
            api_key=api_key,
        )
        self.system_message = SystemMessage(content="你是一个被测模型，请认真回答问题。")

    def respond(self, messages):
        """
        直接调用 DeepSeek 模型，messages 为 [SystemMessage, HumanMessage, ...] 列表
        返回 AI 回复内容字符串
        """
        # 确保 system_message 只加一次
        if not messages or messages[0] != self.system_message:
            messages = [self.system_message] + messages[1:]
        response = self.deepseek.invoke(messages)
        return response.content

    def reset(self):
        """重置状态（如有需要）"""
        pass