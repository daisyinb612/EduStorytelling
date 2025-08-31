import json
import os
from typing import Dict, Any, Optional
from . import prompts 
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from .prompts import CHATPROMPT, JUDGEPROMPT
from langchain_deepseek import ChatDeepSeek

# 从 CHATPROMPT 模板创建一次性的系统消息
# 移到函数外部，这样它只会被创建一次，而不是每次调用节点时都创建

def dialogue_node(state: Dict[str, Any]) -> Dict[str, Any]:
    print("---进入对话准备节点(dialogue_node)---")
    messages = state.get("messages", [])
    if not messages or not hasattr(messages[-1], 'type') or messages[-1].type != 'human':
        raise ValueError("流程错误：需要一个人类输入来启动对话节点。")

    # 获取最新的用户消息
    human_message = messages[-1]
    
    # 组合系统消息和用户消息
    messages_to_model = [SYSTEM_MESSAGE, human_message]

    print(f"已组合系统提示和用户查询 '{human_message.content}'")
    # 返回组合好的消息列表，供模型节点使用
    return {"messages_to_model": messages_to_model}


# def judge_node(state: Dict[str, Any]) -> Dict[str, Any]:
#     print("\n---进入最终评判节点(judge_node)---")

#     final_scores = []
#     try:
#         judge_llm = ChatOpenAI(model="gpt-4o", temperature=0, model_kwargs={"response_format": {"type": "json_object"}})
        
#         # 直接调用 JUDGEPROMPT，不传入任何动态参数
#         judge_prompt_messages = JUDGEPROMPT.format_messages()

#         # 使用静态的prompt调用LLM
#         response = judge_llm.invoke(judge_prompt_messages)
#         score_data = json.loads(response.content)
#         final_scores.append(score_data)
#         print(f"评估完成。")

#     except Exception as e:
#         print(f"错误：调用评判LLM或解析其输出时失败 - {e}")
#         final_scores.append({
#             "score": "error",
#             "reasoning": str(e)
#         })

#     # 保存评分报告
#     try:
#         with open(SCORE_PATH, 'w', encoding='utf-8') as f:
#             json.dump(final_scores, f, ensure_ascii=False, indent=4)
#         print(f"评分报告已成功保存至: {SCORE_PATH}")
#     except Exception as e:
#         print(f"错误：无法保存评分报告 - {e}")

#     return {"scores": final_scores}

class HumanAgent:
    def __init__(self, querylist_path="./data/querylist.json", model_name="deepseek-chat"):
        with open(querylist_path, "r", encoding="utf-8") as f:
            all_cases = json.load(f)
        case = all_cases[0]
        self.type = case.get("type", "")
        # 这里保留 key，方便后续 debug
        self.queries = [(k, v) for k, v in sorted(case["querylist"].items(), key=lambda x: x[0])]
        self.idx = 0
        self.deepseek = ChatDeepSeek(
            model=model_name,
            temperature=0,
            api_key=os.environ.get("DEEPSEEK_API_KEY1"),
        )

    def next_query(self):
        if self.idx < len(self.queries):
            key, query = self.queries[self.idx]
            self.idx += 1
            # 用 CHATPROMPT 生成润色后的提问
            system_prompt = CHATPROMPT.format(THISQUERY=query, type=self.type)
            messages = [SystemMessage(content=system_prompt)]
            response = self.deepseek.invoke(messages)
            return key, query, response.content
        return None, None, None

    def respond(self, messages):
        # 确保 system_message 只加一次
        if not messages or messages[0] != self.system_message:
            messages = [self.system_message] + messages[1:]
        response = self.deepseek.invoke(messages)
        return response.content

    def ask_question(self) -> Optional[str]:
        try:
            question = input("You: ")
            if question.lower() in ['exit', 'quit', 'q']:
                return None
            return question
        except (KeyboardInterrupt, EOFError):
            return None

    def call_deepseek(self, messages):
        """
        调用 DeepSeek 模型，messages 为 [SystemMessage, HumanMessage, ...] 列表，返回 AI 回复内容字符串
        """
        # DeepSeek 支持直接传递 langchain 的消息对象列表
        response = self.deepseek.invoke(messages)
        return response.content

def format_querylist(querylist: dict) -> str:
    # 按照顺序拼接 querylist
    items = sorted(querylist.items(), key=lambda x: x[0])
    return "\n".join([f"{k}: {v}" for k, v in items])