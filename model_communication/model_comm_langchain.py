from dotenv import load_dotenv
import os
from langchain_community.chat_models import ChatZhipuAI, QianfanChatEndpoint, ChatBaichuan
from langchain_community.chat_models.moonshot import MoonshotChat
from langchain_community.chat_models.tongyi import ChatTongyi

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationSummaryMemory, ConversationBufferWindowMemory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

from prompts import PROMPT_TEMPLATES


CHAT_MODELS = {
    'zhipu': ChatZhipuAI,
    'qianfan': QianfanChatEndpoint,
    'moon': MoonshotChat,
    'qwen': ChatTongyi,
    'baichuan': ChatBaichuan
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
    }
}

class ModelCommLangchain():
    def __init__(self, model_name='qianfan'):
        self.log_model_communication_name = r"log.txt"
        load_dotenv()
        chat_model = CHAT_MODELS[model_name](**MODEL_KWARGS[model_name])
        system_template = PROMPT_TEMPLATES['llm_chat']['embrace']
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
    
    def communicate_with_model(self, message):
        self.save_txt(message)
        resp = self.chain.invoke([HumanMessage(content=message)])
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
    
if __name__ == '__main__':
    # communication = ModelCommLangchain(model_name='qianfan')
    communication = ModelCommLangchain(model_name='moon')
    # communication.communicate_with_model('你好')
    communication.communicate_with_model('VScode如何远程连接服务器？')