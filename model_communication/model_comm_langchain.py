from dotenv import load_dotenv
import os
from langchain_community.chat_models import ChatZhipuAI, QianfanChatEndpoint, ChatBaichuan
from langchain_community.chat_models.moonshot import MoonshotChat
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_openai import ChatOpenAI

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationSummaryMemory, ConversationBufferWindowMemory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.callbacks import BaseCallbackHandler

import sys
current_path = os.path.dirname(__file__)
root_path = os.path.abspath(os.path.dirname(current_path) + os.path.sep + ".")
print(root_path)
sys.path.append(root_path)
from text_transfer.prompts import PROMPT_TEMPLATES


CHAT_MODELS = {
    'zhipu': ChatZhipuAI,
    'qianfan': QianfanChatEndpoint,
    'moon': MoonshotChat,
    'qwen': ChatTongyi,
    'baichuan': ChatBaichuan,
    'ollama': ChatOpenAI
}

MODEL_KWARGS = {
    'zhipu': {
        'model': 'glm-4', # glm-3-turbo
        'temperature': 0.1
    },
    'qianfan': {
        'model': 'ERNIE-Bot-turbo', # Qianfan-Chinese-Llama-2-7B
        'temperature': 0.1
    },
    'moon': {
        'model': 'moonshot-v1-32k', # moonshot-v1-8k, moonshot-v1-128k
        'base_url': 'https://api.moonshot.cn/v1',
        'moonshot_api_key': os.getenv('MOONSHOT_API_KEY'),
        'temperature': 0.1
    },
    'qwen': {
        'model': 'qwen-turbo', # qwen-vl-v1 - qwen-vl-chat-v1 - qwen-audio-turbo - qwen-vl-plus - qwen-vl-max
        'top_p': 0.1
    },
    'baichuan': {
        'model': 'Baichuan2-Turbo-192K', # Baichuan2-Turbo
        'temperature': 0.1
    },
    'ollama': {
        'model': 'qwen72b',
        'base_url': 'http://192.168.1.213:11434/v1/',
        'api_key': 'ollama'
    }    
}

class TokenHandler(BaseCallbackHandler):
    def __init__(self, model_name: str, tokens):
        super().__init__()
        self.name = model_name
        self.tokens = tokens
        
    def on_llm_end(self, res, **kwargs) -> None:
        print(res.llm_output)
        if self.name == 'qwen':
            tmp = res.generations[0][0].generation_info["token_usage"]['output_tokens']
        else:
            tmp = res.llm_output["token_usage"]['completion_tokens']
        self.tokens.append(tmp)

class ModelCommLangchain():
    def __init__(self, model_name='qianfan',Comm_type ="duizhan"):
        self.model_name = model_name
        self.history_output_tokens = []
        # self.log_model_communication_name = r"auto_test\log.txt"
        self.log_model_communication_name = r"auto_test\log"+"_"+model_name+"_"+Comm_type+"_.txt"
        load_dotenv()
        chat_model = CHAT_MODELS[model_name](**MODEL_KWARGS[model_name])
        if Comm_type == "duizhan":
            system_template = PROMPT_TEMPLATES['llm_chat']['embrace']
        elif Comm_type == "jieshuo":
            system_template = PROMPT_TEMPLATES['llm_chat']['jieshuo_embrace']
        prompt_template = ChatPromptTemplate.from_messages(
                [("system", system_template), ("user", "{input}")]
            )
        # sys_prompt = SystemMessagePromptTemplate.from_template(system_template)
        # user_prompt = HumanMessagePromptTemplate("{text}")
        # chat_prompt = ChatPromptTemplate.from_messages([sys_prompt, user_prompt])
        
        self.chain = ConversationChain(
            prompt = prompt_template,
            llm = chat_model,
            memory = ConversationBufferWindowMemory(k=3),
            output_parser = StrOutputParser()
        )
        self.msgs = self.chain.memory.buffer
        self.cb = [TokenHandler(self.model_name, self.history_output_tokens)]
    
    def communicate_with_model(self, message):
        self.save_txt(message)           
        resp = self.chain.invoke([HumanMessage(content=message)], config={"callbacks": self.cb})
        resp_str = resp['response']
        self.save_txt(resp_str)
        return resp_str
        
    
    # 基础功能，直接从骁翰那里抄了
    def load_txt(self,file_name):
        # 单纯的读取txt文件，主要是用来读那些key的。
        with open(file_name, 'r', encoding='utf-8') as f:
            neirong = f.read()
            return neirong
        
    def save_txt(self,neirong,file_name=""):
        # 单纯的写入txt文件，主要是用来记录对话的。
        if file_name == "":
            file_name = self.log_model_communication_name
        with open(file_name, 'a', encoding='utf-8') as f:
            f.write(neirong+"\n")
        return
    
    def get_tokens(self):
        # 获取token数
        token_all = 0 
        for output_token in self.history_output_tokens:
            token_all = token_all + output_token
        str_buffer ="==========当前模型为" + self.model_name + "，当前token数为" + str(token_all)
        self.save_txt(str_buffer)
        print(str_buffer)
        
if __name__ == '__main__':
    communication = ModelCommLangchain(model_name='ollama')
    # communication = ModelCommLangchain(model_name='moon')
    # communication.communicate_with_model('你好')
    test_str = """我方obj_id为MainBattleTank_ZTZ100_3的坦克位置在(2.59297,39.72039)处 \n
                    我方obj_id为missile_truck0的导弹发射车位置在(2.6228,41.6363)处 \n
                    敌方obj_id为MainBattleTank_ZTZ200_1的坦克位置在(2.68121,39.71009)处 \n
                    敌方obj_id为WheeledCmobatTruck_ZB200_3的步战车位置在(2.70102,39.71207)处"""
    ret = communication.communicate_with_model(test_str)
    # print(ret)
    print(communication.history_output_tokens)