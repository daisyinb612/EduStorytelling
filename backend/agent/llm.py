from openai import OpenAI
from datetime import datetime
import json
# from module import db, History, ChatHistory
from flask import Flask
# from flask_cors import CORS
from copy import (
    deepcopy,
)
from agent.prompt import PROMPT # 只导入 PROMPT 字典

# app = Flask(__name__, template_folder='template')
# CORS(app)
#
# app.config[
#     'SQLALCHEMY_DATABASE_URI'] = 'mysql://root:Gzn_020619@rm-uf60o300c5g94r9u4ko.mysql.rds.aliyuncs.com:3306/test1'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.config['JWT_SECRET_KEY'] = '9X#$2q8Wp!z*Y&fD7g+2jC5h^'
#
# db.init_app(app)

from sql.chat_db import Chat
from agent.prompt import *


with open('./agent/model_list.json', 'r', encoding='utf-8') as f:
    model_list = json.load(f)

chat_model = model_list['chat_model']["doubao1.6"]
pic_model = model_list['pic_model']['dall-e-3']

class LLM(object):
    def __init__(self, chat_model, pic_model, temperature=0.8):
        self.chat_model_name = chat_model['model_name']
        self.pic_model_name = pic_model['model_name']
        self.chat_client = OpenAI(api_key=chat_model['api_key'], base_url=chat_model['base_url'])
        self.pic_client = OpenAI(api_key=pic_model['api_key'], base_url=pic_model['base_url'])
        self.temperature = temperature

        self.fix_json = '''
        I will provide text with formatting issues, and your task is to output the corrected JSON string. 
        When outputting, do not repeat the task requirements, just provide the corrected JSON string.
        '''
        self.storyline_help = '''
        Assume you are a drama playwriting teacher, and your task is to provide me information and help in writing a storyline with specific character. 
        Please guide me in using two or three sentences to summarize the story I want to tell. When outputting, do not repeat the task requirements.
        If the input is Chinese, please output Chinese.
        If the input is English, please output English.
        '''
        self.role_help = '''
        Assume you are a drama playwriting teacher,and your task is to provide me with guidance or help in crafting characters.
        I will provide ###LOGLINE###, ###CHARACTERLIST###, and ###MYQUESTION### in the following conversation. When outputting, do not repeat the task requirements.
        Please provide concise and effective guidance in three sentences or less.
        If the input is Chinese, please output Chinese.
        If the input is English, please output English.
        '''
        self.plot_help = '''
        Assume you are a drama playwriting teacher,and your task is to provide me with guidance or help in crafting plots.
        I will provide ###LOGLINE###, ###CHARACTERLIST###,and ###MYQUESTION### in the following conversation. When outputting, do not repeat the task requirements.
        Please provide concise and effective guidance in three sentences or less.
        If the input is Chinese, please output Chinese.
        If the input is English, please output English.
        '''
        self.scene_help = '''
        Assume you are a drama playwriting teacher,and your task is to provide me with guidance or help in crafting scenes.
        I will provide ###LOGLINE###、###OUTLINE###和###MYQUSETION### in the following conversation.
        The story outline includes###PLOTNAME###,、###PLOTNAME###,###PLOTBEAT###and###CHARACTERLISTE###for each plot。
        When outputting, do not repeat the task requirements.
        Please provide concise and effective guidance in three sentences or less.
        If the input is Chinese, please output Chinese.
        If the input is English, please output English.
        '''
        self.dialogue_list_help = '''
        Assume you are a drama playwriting teacher,and your task is to provide me with guidance or help in crafting dialogues.
        I will provide ###LOGLINE###、###OUTLINE###和###MYQUSETION### in the following conversation.
        The story outline includes###PLOTNAME###,、###PLOTNAME###,###PLOTBEAT###and###CHARACTERLISTE###for each plot。
        When outputting, do not repeat the task requirements.
        Please provide concise and effective guidance in three sentences or less.
        If the input is Chinese, please output Chinese.
        If the input is English, please output English.
        '''
        self.CHARACTERLIST_PROMPT = PROMPT['character_list']
        self.OUTLINE_PROMPT = PROMPT['outline']
        self.setting_dialogue_create = PROMPT['dialogue_list']
        # self.rich_sentence = '''
        # Assume you are a playwright.读#句子#，符合#角色# 根据#修改意见#
        # If the ###LOGLINE### is Chinese, please output Chinese.
        # '''
        self.history = None

    def save_history(self, question, answer, prompt, user_id, opera_id, chat_id=None):
        if chat_id is None:
            new_history = [{"role": "system", "content": prompt}]
        else:
            new_history = [{"role": "system", "content": prompt}]
            chat = Chat.get_chat_by_id(chat_id, user_id)
            history = chat.chat_AI  # 使用属性访问而不是字典访问
            # 确保 history 是列表类型
            if isinstance(history, str):
                print(f"Warning: chat_AI is string '{history}', converting to empty list")
                history = []
            elif history is None:
                history = []
            
            for row in history:
                new_history.append(row)
        new_history.append({"role": "user", "content": question})
        new_history.append({"role": "assistant", "content": answer})

        if chat_id is None:
            chat = Chat.create_chat(user_id, opera_id, new_history)
        else:
            chat = Chat.update_chat_by_id(chat_id, user_id, new_history)
        return

    def chat(self, question, prompt):
        new_messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": question},
        ]

        try:
            response = self.chat_client.chat.completions.create(
                model=self.chat_model_name,
                messages=new_messages,
                top_p=0.7,
                stream=True,
            )
        except Exception as e:
            print('chat_client error:', e)
            print('current model is: ', self.chat_model_name)
        answer = ''
        print('思考中', end='\n')
        for trunk in response:
            if trunk.choices and len(trunk.choices) > 0:
                if trunk.choices[0].delta and trunk.choices[0].delta.content:
                    print(trunk.choices[0].delta.content, end='')
                    answer += trunk.choices[0].delta.content
        print('\n提问完成\n')
        return answer

    def ask(self, question, prompt, user_id, opera_id, chat_id=None, save_history=False):
        if not chat_id:
            new_messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": question},
            ]
        else:
            new_messages = [{"role": "system", "content": prompt}]
            chat = Chat.get_chat_by_id(chat_id, user_id)
            history = chat.chat_AI
            # 确保 history 是列表类型，如果是字符串则转换为空列表
            if isinstance(history, str):
                print(f"Warning: chat_AI is string '{history}', converting to empty list")
                history = []
            elif history is None:
                history = []
            
            for row in history:
                new_messages.append(row)
            new_messages.append({"role": "user", "content": question})
        try:
            response = self.chat_client.chat.completions.create(
                model=self.chat_model_name,
                messages=new_messages,
                top_p=0.7,
                stream=True,
            )
        except Exception as e:
            print('chat_client error:', e)
            print('current model is: ', self.chat_model_name)
        answer = ''
        print('思考中', end='\n')
        for trunk in response:
            if trunk.choices and len(trunk.choices) > 0:
                if trunk.choices[0].delta and trunk.choices[0].delta.content:
                    print(trunk.choices[0].delta.content, end='')
                    answer += trunk.choices[0].delta.content
        print('\n提问完成\n')
        if save_history:
            self.save_history(question, answer, prompt, user_id, opera_id, chat_id)
        return answer

    def create_picture(self, prompt, user_id, opera_id):
        try:
            print('generating picture using: ', self.pic_model_name)
            response = self.pic_client.images.generate(
                model=self.pic_model_name,
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            image_url = response.data[0].url
            print('generate image_url: ', image_url)
            # self.save_history(question=prompt, answer="", prompt="", user_id=user_id, opera_id=opera_id)
            return image_url
        except Exception as e:
            print('pic_client error:', e)
            print('current model is: ', self.pic_model_name)

    def analyze_answer(self, text):
        try:
            first_index = text.find('[')
            last_index = text.rfind(']')
            text = text[first_index:last_index + 1]
            json_object = json.loads(text)
            print(text)
            return json_object
        except:
            print("模型输出格式不符合json格式，将重新使用模型修正格式问题")
            text = self.chat(question=text, prompt=self.fix_json)
            json_object = self.analyze_answer(text=text)
            return json_object

global_llm = LLM(chat_model=chat_model, pic_model=pic_model)