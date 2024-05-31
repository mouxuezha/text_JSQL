# 这个先以mouxuezha比较熟悉的百度文心千帆来实现。

import requests
import qianfan
import os 

class model_communication():
    def __init__(self):
        self.__init_AKSK()
        pass

    def __init_AKSK(self):
        # 初始化百度文心千帆API密钥
        print("model_communication: using qianfan")
        # 通过环境变量传递（作用于全局，优先级最低）
        self.qianfan_access_key = self.load_txt("AK.txt")
        self.qianfan_security_key = self.load_txt("SK.txt")
        os.environ["QIANFAN_ACCESS_KEY"] = self.qianfan_access_key
        os.environ["QIANFAN_SECRET_KEY"] = self.qianfan_security_key
        self.chat_comp = qianfan.ChatCompletion()
        pass

    def communicate_with_model(self, message):
        # 调用百度文心千帆模型

        # 下面是一个与用户对话的例子
        msgs = qianfan.Messages()
        while True:
            msgs.append(input("输入："))         # 增加用户输入
            resp = self.chat_comp.do(messages=msgs)
            print(resp)                 # 模型的输出
            msgs.append(resp)            # 追加模型输出        
        pass
    def load_txt(self,file_name):
        # 单纯的读取txt文件，主要是用来读那些key的。
        
        with open(file_name, 'r', encoding='utf-8') as f:
            neirong = f.read()
            return neirong
        
if __name__ == '__main__':
    communication = model_communication()
    communication.communicate_with_model('你好')