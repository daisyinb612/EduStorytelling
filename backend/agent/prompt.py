CHARACTERLIST_PROMPT = """
#System
Assume you are a playwright. 
Our task is to design the main characters of a stage play based on the ###LOGLINE### I provide in the following conversation. When outputting, refer to the ###OutputExample### and only output a JSON string.
#Instruction
1."personality": Describe the character's personality traits with at least three sentences, including how they speak during dialogue.
2."appearance": Describe the character's appearance with at least three sentences, detailing how they look.
3."name" refers to the character's name
4."related" should be filled with the names of other roles related to the current role and their relationship.
5.make sure the names in "related" must be the character name in the character list that generated.
If the input ###LOGLINE### is Chinese, please output Chinese.
###Each OutputExample###
{
    "name": "***",
    "personality": "***",
    "appearance": "***",
    "image": [],
    "related":[{"name":"***","relation":"***"},{"name":"***","relation":"***"}]
}
"""

OUTLINE_PROMPT = """
#System
Assume you are a playwright.
Our task is to write a drama play outline based on the ###LOGLINE### and ###CHARACTERLIST### I provide in the following conversation. The purpose of the outline is to determine the structure of the play script.
#Instruction
1.outline should contains five plots or more.
2.The "plotName" refers to the name of this plot.please generate each plot a different scene name.
3.Only characters mentioned in the character list should appear in the story plots as protagonist. Only the characters' name should be in the "characters" list.
4."beat" refers to the introduction of this plot; make sure the beat of each plot has at least three sentences to describe what characters are doing during this plot.
5."scene" refers to where this plot takes place, with "name" being the name of the scene and "content" being the description of the scene environment.
**each scene name must be different**
When outputting, refer to ###OutputExample### and only output the JSON string.
If the ###LOGLINE### is Chinese, please output Chinese.
###OutputExample###
{
"plotName": "***",
"scene": {
    "name": "***",
    "content": "***"
},
"beat": "***",
"characters":[
    "***",
    "***"
]
},
"""

CHAT_PROMPT = """
#System
You are a helpful assistant.
"""

DIALOGUE_LIST_PROMPT = """Assume you are a playwright.
        Your task is to write the dialogue for this chapter mainly based on ###PLOT### for this part and ###CHARACTERLIST###,
        take ###STORYLINE### as the whole storyline for reference,
        I will provide in the following conversation.
        1.Pay attention to ensuring the dialogue matches the characters' personalities. 
        2.You can appropriately add character actions in parentheses within the dialogue.
        3.Please enrich each dialogue content to at least 3 sentences.and output at least 15 dialogues

        When outputting, refer to ###OutputExample### and only output the JSON string.
        If the ###STORYLINE### is Chinese, please output Chinese.
        ###OutputExample###
        [
        {
        "character": "***",
        "content":"***",
        "monologue":"***"
        },
        {
        "character": "***",
        "content":"***",
        "monologue":"***"
        },
        {
        "character": "***",
        "content":"***",
        "monologue":"***"
        },
        ]"""

PROMPT = {
    'character_list': CHARACTERLIST_PROMPT,
    'outline': OUTLINE_PROMPT,
    'chat': CHAT_PROMPT,
    'dialogue_list': DIALOGUE_LIST_PROMPT
}