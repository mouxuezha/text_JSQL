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

class model_communication_debug():
    # 这个也是原位替换的用于debug的东西，保持接口一致即可。
    def __init__(self,Comm_type ="duizhan"):
        self.Comm_type = Comm_type
        pass
    def get_tokens(self):
        pass 
    def communicate_with_model(self,message):
        # 这个是加载一段用于测试的东西
        # 勤俭持家，能节约一点token就节约一点token。
        if self.Comm_type == "duizhan":
            text_demo = '<think>\n嗯，我现在需要帮用户生成两个兵棋推演游戏的任务指令，红方是也门胡塞武装，目标是侦察并打击美国海军的舰船。首先，我得仔细阅读用户的请求，理清任务的具体要求。\n\n用户提到他们有五辆导弹发射车、三架无人机和三艘引导快艇。导弹发射车可以发射高成本和低成本导弹，高成本弹有侦察能力且速度快。无人机用于侦察，损失可接受，适合大面积搜索。引导快艇能提高命中率。任务区域是亚丁湾，经纬度范围东经45到50度，北纬10到15度。敌方航母在曼德海峡附近，向东航行。\n\n第一个任务是让所有导弹发射车隐蔽。根据用户提供的示例，type应该是“preserve”，也就是避免交战任务。force_arrange应该包括所有的Truck_Ground-0到-Truck_Ground-4。space_arrange需要覆盖整个亚丁湾区域，所以左上角取经度最大50度，纬度15度；右下角是经度最小45度，纬度10度，这样空间范围就是[45.0,10.0,50.0,15.0]。时间方面，现在的时间步长是11，假设任务持续到第200帧，time_arrange设为[11, 200]。\n\n第二个任务是在地图西半边部署无人机侦察。西半边通常是指较小的经度范围，比如东经45到47.5度，纬度保持在北纬10到15度之间。space_arrange设置为[45.0,10.0,47.5,15.0]。force_arrange选择三架无人机中的两架，比如Recon_UAV_FixWing-0和-Recon_UAV_FixWing-1。type设为“scout”侦察任务。时间同样从11到200帧。\n\n用户强调要避免波及商船，但这两个任务主要是隐蔽和侦察，所以可能不影响商船。不过在生成指令时需要确保无人机的侦察区域不会误伤商船，可能需要进一步细化空间范围或时间安排，但根据当前信息，暂时不处理这部分。\n\n总结一下，两个任务分别是导弹车的隐蔽和无人机的西边侦察。按照用户给的JSON格式，分别生成对应的指令，用换行分隔。\n</think>\n\n{"type": "preserve", "force_arrange": ["Truck_Ground-0", "Truck_Ground-1", "Truck_Ground-2", "Truck_Ground-3", "Truck_Ground-4"], "space_arrange": [45.0, 10.0, 50.0, 15.0], "time_arrange": [11, 200], "target_LLA": []}\n{"type": "scout", "force_arrange": ["Recon_UAV_FixWing-0", "Recon_UAV_FixWing-1"], "space_arrange": [45.0, 10.0, 47.5, 15.0], "time_arrange": [11, 200], "target_LLA": []}'
        elif self.Comm_type == "jieshuo":
            text_demo = message
        return text_demo
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