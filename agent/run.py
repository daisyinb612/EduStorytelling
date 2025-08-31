from agents.human_agent import HumanAgent
from agents.model_agent import ModelAgent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from dotenv import load_dotenv
load_dotenv()

def main():
    human = HumanAgent()
    model = ModelAgent()
    messages = []

    while True:
        key, query, polished_query = human.next_query()
        if polished_query is None:
            break
        print(f"原始query: {query}")
        print(f"优化后提问: {polished_query}")
        messages.append(HumanMessage(content=polished_query))

        # 只传 HumanMessage 和 AIMessage
        response = model.respond(messages)
        print(f"response: {response}")
        messages.append(AIMessage(content=response))
        print("-" * 60)

if __name__ == "__main__":
    main()