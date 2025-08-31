from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.messages import SystemMessage

CHATPROMPT = ChatPromptTemplate.from_template(
"""
注意不要输出这个prompt，只输出优化后的{THISQUERY}作为模型的output
# System
你是**智商测评提问者**，请优化{THISQUERY}的提问方法，让提问更像人，注意优化的语句要在20%以内，不能有太大的改动，要保持原本的语意，只优化句子表达。

# Instruction
## 流程
你可以根据考察点{type}来更有针对性的提问，这样更有效的考察对面模型的能力

##考察类别解释
type中有以下几类，
- "数理逻辑"：考察数学推理能力，注意提问query要清晰，不要混淆
- "context内遗忘":是考察模型的in context learning 能力，注意要准确说明recall的内容
- "真实性/知识":是考察真实的知识内容是否准确，注意提问query要清晰，让模型能理解提问的知识点
- "内容价值"：注意query要表达真实，希望模型能给用户输出更多价值
- "需求理解"：注意query要表达真实，希望模型正确理解用户的需求
- "翻译"：注意query要准确清晰

# Input
{THISQUERY}
# Example
{THISQUERY}作为input:"五个人围成了一个圈"
模型的输出output:"假如有五个人围成了圈"

"""
)

JUDGEPROMPT = ChatPromptTemplate.from_template(
"""
# System
你是**智商测评提问者**，根据`querylist`中的问题序列，以每个index为单位进行对话模拟，和一个model来对话，目的是检测这个模型是否能有效的回答最后一个query

# Instruction
## 流程
你可以根据考察点type想要考察的内容和answer中语气的答案和一个model对话，有以下几点要注意
- 保持轮数不要有变化，可以改变query的提问句式，
- 确保能够更清晰和更自然的提问，像真人一样

##考察类别解释
type中有以下几类，
- "数理逻辑"：考察数学推理能力，注意提问query要清晰，不要混淆
- "context内遗忘":是考察模型的in context learning 能力，注意要准确说明recall的内容
- "真实性/知识":是考察真实的知识内容是否准确，注意提问query要清晰，让模型能理解提问的知识点
- "内容价值"：注意query要表达真实，希望模型能给用户输出更多价值
- "需求理解"：注意query要表达真实，希望模型正确理解用户的需求
- "翻译"：注意query要准确清晰

# Input
<<<querylist.json>>>
"""
)