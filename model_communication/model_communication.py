# 这个先以mouxuezha比较熟悉的百度文心千帆来实现。

import requests
import qianfan
import os 

class model_communication():
    def __init__(self):
        
        self.log_model_communication_name = r"C:\Users\42418\Desktop\2024ldjs\EnglishMulu\text_JSQL\model_communication\log.txt"
        self.__init_AKSK()
        pass

    def __init_AKSK(self):
        # 初始化百度文心千帆API密钥
        # print("model_communication: using qianfan")
        self.save_txt("model_communication: using qianfan")
        # 通过环境变量传递（作用于全局，优先级最低）
        self.qianfan_access_key = self.load_txt(r"C:\Users\42418\Desktop\2024ldjs\EnglishMulu\text_JSQL\model_communication\AK.txt")
        self.qianfan_security_key = self.load_txt(r"C:\Users\42418\Desktop\2024ldjs\EnglishMulu\text_JSQL\model_communication\SK.txt")
        os.environ["QIANFAN_ACCESS_KEY"] = self.qianfan_access_key
        os.environ["QIANFAN_SECRET_KEY"] = self.qianfan_security_key
        self.chat_comp = qianfan.ChatCompletion()
        self.msgs = qianfan.Messages()
        pass

    def communicate_with_model(self, message):
        # 调用百度文心千帆模型
        self.save_txt(message)
        # 下面是一个与用户对话的例子
        # msgs = qianfan.Messages()

        # msgs.append(input("输入："))         # 增加用户输入
        self.msgs.append(message) # 这个巨大的列表就让它自己在这里面维护吧，说大也大不到哪儿去应该。
        resp = self.chat_comp.do(messages=self.msgs)
        resp_str = resp.body["result"]
        # print(resp_str)                 # 模型的输出
        self.save_txt(resp_str)
        self.msgs.append(resp)            # 追加模型输出     
   
        return resp_str
    
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
    communication = model_communication()
    communication.communicate_with_model('你好')
    communication.communicate_with_model('VScode如何远程连接服务器？')