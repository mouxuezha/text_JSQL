from dotenv import load_dotenv
from langchain_community.chat_models import ChatZhipuAI, QianfanChatEndpoint
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationSummaryMemory, ConversationBufferMemory
from langchain_core.output_parsers import StrOutputParser

CHAT_MODELS = {
    'zhipu': ChatZhipuAI,
    'qianfan': QianfanChatEndpoint
}

MODEL_KWARGS = {
    'zhipu': {
        'model': 'glm-4',
        'temperature': 0.1
    },
    'qianfan': {
        'model': 'ERNIE-Bot-turbo',
        'temperature': 0.1
    }
}

class ModelCommLangchain():
    def __init__(self, model_name='qianfan'):
        self.log_model_communication_name = r"log.txt"
        load_dotenv()
        chat_model = CHAT_MODELS[model_name](**MODEL_KWARGS[model_name])
        self.chain = ConversationChain(
            llm = chat_model,
            memory = ConversationBufferMemory(llm = chat_model),
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
    communication = ModelCommLangchain(model_name='qianfan')
    # communication.communicate_with_model('你好')
    communication.communicate_with_model('VScode如何远程连接服务器？')