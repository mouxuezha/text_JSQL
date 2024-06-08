# 这个先以mouxuezha比较熟悉的百度文心千帆来实现。

import requests
import qianfan
import os 

class model_communication():
    def __init__(self):
        
        self.log_model_communication_name = r"model_communication\log.txt"
        self.__init_AKSK()
        pass

    def __init_AKSK(self):
        # 初始化百度文心千帆API密钥
        # print("model_communication: using qianfan")
        self.save_txt("model_communication: using qianfan")
        # 通过环境变量传递（作用于全局，优先级最低）
        self.qianfan_access_key = self.load_txt(r"model_communication\AK.txt")
        self.qianfan_security_key = self.load_txt(r"model_communication\SK.txt")
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
    
    def communicate_with_model_debug(self,message):
        # 这个是加载一段用于测试的东西
        # 勤俭持家，能节约一点token就节约一点token。
        text_demo = "好的，按照你的格式给出作战指令：1. [move, ArmoredTruck_ZTL100_0, x=2.59, y=39.72], 移动我方无人战车ArmoredTruck_ZTL100_0到(2.59,39.72)处。2. [move, ArmoredTruck_ZTL100_1, x=2.59, y=39.72], 移动我方无人战车ArmoredTruck_ZTL100_1到(2.59,39.72)处。3. [move, Howitzer_C100_0, x=2.59, y=39.72], 移动我方自行迫榴炮Howitzer_C100_0到(2.59,39.72)处。4. [move, Infantry0, x=2.59, y=39.72], 移动我方步兵Infantry0到(2.59,39.72)处。5. [move, Infantry1, x=2.59, y=39.72], 移动我方步兵Infantry1到(2.59,39.72)处。6. [move, MainBattleTank_ZTZ100_0, x=2.59, y=39.72], 移动我方坦克MainBattleTank_ZTZ100_0到(2.59,39.72)处。7. [move, MainBattleTank_ZTZ100_1, x=2.59, y=39.72], 移动我方坦克MainBattleTank_ZTZ100_1到(2.59,39.72)处。8. [move, MainBattleTank_ZTZ100_2, x=2.59, y=39.72], 移动我方坦克MainBattleTank_ZTZ100_2到(2.59,39.72)处。9. [move, MainBattleTank_ZTZ100_3, x=2.59, y=39.72], 移动我方坦克MainBattleTank_ZTZ100_3到(2.59,39.72)处。10. [move, ShipboardCombat_plane0, x=2.59, y=39.72], 移动我方无人机ShipboardCombat_plane0到(2.59,39.72)处。...接下来的指令按照上述格式，给出每一步行动的指令..."
        return text_demo
    
    def communicate_with_model_single(self,message):
        # 由于文心有长度限制，连续走多轮调用会报错，所以这里采取一个丑陋的变通处理，每一步都只输入initiate和当前态势，重开一个序列。
        self.__init_AKSK()
        try:
            resp_str = self.communicate_with_model(message)
        except:
            resp_str = "文心寄了，下一轮看运气罢。"
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