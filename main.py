# 这个是主函数，到时候就运行这个就完事了。
from agent_guize.enemy_AI.agent.agent_dispatch import agent_dispatch
# from agent_guize.me_AI.agent.agent_dispatch import agent_dispatch
# 原则上应该分开两个文件夹导入的，但是现在红蓝方都是我的，所以就也没什么所谓了。

from agent_guize.Env import Env,Env_demo
from agent_guize.tools import get_states, auto_state_filter, auto_state_compare2 , auto_save_overall, auto_save, auto_save_file_name, auto_state_compare
from text_transfer.text_transfer import text_transfer, text_demo, text_demo_blue
from text_transfer.stage_prompt import StagePrompt
from model_communication.model_communication import model_communication, model_communication_debug
from model_communication.model_comm_langchain import ModelCommLangchain
from dialog_box.dialog_box_debug import *
from socket_communication.socket_server import *
from socket_communication.socket_client import *
from socket_communication.socket_debug import *

from TTS.TTS_interface import TTS_interface

from plan_interface.plan_interface import plan_interface

import json
import time 
import argparse
import sys,os,pickle
from importlib import import_module
import random

import threading

from PySide6 import QtCore, QtWidgets, QtGui

class command_processor(QtCore.QThread):
    
    def __init__(self,dialog_box, Comm_type ="duizhan",role="offline",**kargs):
        super().__init__()
        self.runnig_location = r"auto_test"
        self.log_file = r'overall_result.txt'
        self.dialog_box = dialog_box

        if "flag_auto_CraftGame" in kargs:
            self.flag_auto_CraftGame = kargs["flag_auto_CraftGame"]
        else:
            self.flag_auto_CraftGame = False
        
        if self.flag_auto_CraftGame:
            self.turn_on_CraftGame()


        if role == "offline":
            # 那就是无事发生
            self.role = "offline"
            self.args = self.__init_net()
            self.__init_env()
            self.__init_agent()
            if "config" in kargs:
                self.config = kargs["config"]  
            else:
                self.config = {}
        else:
            self.__init_socket(role =role, config=kargs["config"])
            self.config = kargs["config"] # 后面需要的配置项越加越多，还是专门开一个设置的来弄一下好了。

        if "flag_server_waiting" in self.config:
            pass
        else:
            # 没有的话补充默认值。
            self.config["flag_server_waiting"]=False
        
        if "communicator" in kargs:
            # 这个不是和大模型通信，这个是和前端交互的。
            self.communicator = kargs["communicator"]
        else:
            self.communicator = None

        self.text_transfer = text_transfer()
        self.stage_prompt = StagePrompt(flag_kaiguan=False) # 这里可以改开不开stage，开了可以用于调试。
        self.LLM_model = "qianfan" # 这里可以改，默认是qianfan,还有智谱啥的
        # self.model_communication = model_communication_debug() # 这里如果用debug就是实际上不开大模型
        # 这里还得把红蓝方作为一个参数传进去。
        self.model_communication = ModelCommLangchain(model_name=self.LLM_model,Comm_type=Comm_type,role=role)
        # 要用多个的话等后面再来改罢。

        # 解说的直接弄进去也没啥不好的。都置为False就是直接不要解说功能了，应该能够不影响程序其他部分的使用
        config_TTS = {"flag_generate":True,"flag_play":True}
        self.shishi_TTS = TTS_interface(config =config_TTS )
        self.shishi_TTS.run_mul() # 反正启动线程嘛，在哪启动不是启动。
        
        self.status= {} # 这个是我方的
        self.detected_state = {} # 这个是敌方的
        self.timestep = 0 
        self.flag_human_interact = False #这个用来标志当前时间步是否引入人类交互。
        self.flag_regular_interacte = True # 这个用来改是不是定时和大模型交互的，关了就是只有人说话才交互。
        self.human_order = "" # 这个用来常态化地存人类交互指令，以防人类意图只出现一帧就被盖了

        # 搞一个用来存复盘的东西。
        self.fupan_pkl = {} # {timestep: {"command":command_list, "all_str":all_str, "response_str":response_str} }
        self.flag_fupan = False # 用来标记当前是否在复盘。
        self.flag_finished = False 
        pass
    
    # def __init_dialog_box(self):
    #     # 初始化对话框
    #     app = QtWidgets.QApplication([])
    #     self.dialog_box = MyWidget()
    #     self.dialog_box.resize(800, 300)
    #     self.dialog_box.show()
    #     sys.exit(app.exec())
    #     pass
    
    def __init_env(self):
        self.max_episode_len = self.args.max_episode_len
        self.env = Env(self.args.ip, self.args.port)

    def __init_net(self):
        parser = argparse.ArgumentParser(description='Provide arguments for agent.')
        parser.add_argument("--ip", type=str, default="127.0.0.1", help="Ip to connect")
        # parser.add_argument("--ip", type=str, default="192.168.43.93", help="Ip to connect")
        parser.add_argument("--port", type=str, default=20001, help="port to connect")
        parser.add_argument("--epochs", type=int, default=200, help="Number of training epochs to run")  # 设置训练轮次数
        parser.add_argument("--max-episode-len", type=int, default=5000, help="maximum episode length")
        net_args = parser.parse_args()
        return net_args

    def __init_agent(self):
        # 这里面应该不要含有需要给后端发东西的内容，以便调试。
        self.redAgent = agent_dispatch(player="red")
        self.blueAgent = agent_dispatch(player="blue")
        self.red_deploy_location = self.runnig_location + r'\guize\reddeploy'
        self.blue_deploy_location = self.runnig_location + r'\guize\bluedeploy'
        # self.redAgent.set_deploy_folder(self.red_deploy_location)
        # self.blueAgent.set_deploy_folder(self.blue_deploy_location)
    
    def __init_socket(self, role, config:dict):
        if role == "server":
            # 只有server是真的需要跟平台通信的，player模式的话是不需要跟平台通信的。
            # 同时，如果分了server和player，那么server这头就不和大模型通信了就。
            self.role = "server"
            self.__init_socket_server(config)
            # 这些是跟平台通信的东西，自然只需要在本线程是服务器的时候才需要来。
            self.args = self.__init_net()
            self.__init_env()
            self.__init_agent()
        elif role == "red_player":
            self.role = "red_player"
            self.__init_socket_client(config)
        elif role == "blue_player":
            self.role = "blue_player"
            self.__init_socket_client(config)  
        else:
            raise Exception("invalid role in main_loop.__init_socket, G.")      

    def __init_socket_server(self,config:dict):
        # 初始化一些本地网络通信的东西。
        self.red_response_str = ""
        self.blue_response_str= ""
        # config = {"red_ip":"192.168.1.117", "red_port": "20001",
        #           "blue_ip": "192.168.1.117", "blue_port": "20002" }    

        return # 这个放到dialog box server里面去弄了
        self.socket_server = socket_server_2player(config,dialog_box=self.dialog_box)
        self.socket_server.run_mul() # 这个得在合适的敌方给它开起来

    def __init_socket_client(self,config:dict):
        if "socket_debug_model" in config:
            socket_debug_model = config["socket_debug_model"]
        else:
            socket_debug_model = "net_debug"

        if socket_debug_model == "local_debug":
            self.socket_client = socket_debug(self.dialog_box, ip=config["red_ip"],port=config["red_port"])
        elif socket_debug_model == "net_debug":
            # 看自己是红蓝方了。
            if self.role == "red_player":
                self.socket_client = socket_client(self.dialog_box, ip=config["red_ip"],port=config["red_port"])
            elif self.role == "blue_player":
                self.socket_client = socket_client(self.dialog_box, ip=config["blue_ip"],port=config["blue_port"])
        else:
            raise Exception("undifined socket_model")

    def get_agent_out(self,role="blue",location = r""):
        # 这个是搞一个方便地装载外部agent的接口。从去年劳动竞赛的craft manager的基础上开发出来的。
        # 2024，这个还得改，但是等用的时候再改吧，效率优先
        if role == "blue":
            # blue_location = location + r'\python1\AI'
            blue_location = location + r'\python1'
            # blue_name = 'BlueAgent'
            blue_name = 'blue_agent'
            agent_out = self.import_certain_file(blue_location,blue_name)
            self.blueAgent = agent_out.BlueAgent()
        elif role == "red":
            red_location = location + r'\python1\AI'
            # red_name = 'RedAgent'
            red_name = 'red_agent'
            agent_out = self.import_certain_file(red_location,red_name)
            self.redAgent = agent_out.RedAgent()    
        # return agent_out
        pass 

    def import_certain_file(self, location, name):

        # 行吧，用点阳间的方式。
        sys.path.insert(0, location)
        try:
            sys.path.append(location+ r"\AI")
            try:
                shishi = import_module(name=name)
            except:
                shishi = import_module(name="AI."+name)
            del sys.path[0]
        except:
            print("Craft_Manager: attention, other file included")
            sys.path.insert(0, location + r"\AI")
            sys.path.insert(0, location)
            sys.path.insert(0, location + r"\agent")
            shishi = import_module(name=name)
            del sys.path[0]
            del sys.path[0]
            del sys.path[0]
        del sys.path[0]
        del sys.path[0]
        del sys.path[-1]

        return shishi
    
    def set_communicator(self,communicator):
        # 这个是用来在尽量不动原来的东西的基础上把通信类传进来。
        self.communicator = communicator

    def add_fupan_info(self, time_step, command, all_str, response_str):
        fupan_step_single = {"command":command, "all_str":all_str, "response_str":response_str}

        self.fupan_pkl[time_step]=fupan_step_single

    def save_fupan_info(self):
        # 这么搞其实有风险，每存一次都会生成一个不一样的。但是先不管了
        log_file = self.runnig_location + r'\auto_test_log' + str(0) + r'.pkl'
        for i in range(114514): # 生成一个不会重复的文件名
            if os.path.exists(log_file):
                log_file = self.runnig_location + r'\auto_test_log' + str(i+1) + r'.pkl'
            else:
                break         
        
        # 然后把复盘信息存进去
        pickle.dump(self.fupan_pkl, open(log_file, 'wb'))
    
    def load_fupan_info(self, log_file_name_relative:str):

        # 读取特定的复盘文件。
        if log_file_name_relative.find('pkl') == -1:
            log_file_name_relative = log_file_name_relative + r'.pkl'
        if log_file_name_relative.find('\\') == -1:
            log_file_name_relative = '\\' + log_file_name_relative
        log_file = self.runnig_location + log_file_name_relative
        self.fupan_pkl = pickle.load(open(log_file, 'rb'))
        pass

    
    def run(self):
        # 这个是Qthread要求实现的主循环
        while True:
            if self.dialog_box.p_status == "on":
                print("command_processor is running as "+self.role)
                if (self.role == "offline"):
                    self.main_loop()
                elif (self.role == "server"):
                    self.main_loop_wrap()
                elif (self.role == "red_player") or (self.role=="blue_player"):
                    self.main_loop_client() # 这不一样的，得进行一点定制才行，用于实现客户端电脑和大模型的通信。
            else:
                print("command_processor is off")
                time.sleep(1)
                pass

    def run_one_step(self,additional_str=""):
        # 从agent把态势拿出来
        self.status, self.detected_state= self.redAgent.get_status()

        # 把态势转成大模型能看懂的文本形式
        # status_str = self.text_transfer.status_to_text(self.status) # 这个是原版的
        status_str = self.text_transfer.status_to_text2(self.status) # 这个是简化版的

        detected_str = self.text_transfer.detected_to_text(self.detected_state)
        # 再加一个子航给整的“人类指挥员注意力管理机制”，更新到dialog_box里面。
        zhuyili_str = self.text_transfer.turn_taishi_to_renhua(self.status, self.detected_state)

        # 把新的状态压入到解说的那一组线程里面去。
        self.shishi_TTS.add_status_list(status_str+detected_str)        

        # 检测是否人混的干预，有的话也弄进去
        flag_human_intervene, status_str_new = self.human_intervene_check(zhuyili_str + status_str + detected_str)

        # 增加态势阶段的提示。
        stage_str = self.stage_prompt.get_stage_prompt(self.timestep)
        # all_str = status_str + detected_str + status_str_new  +additional_str + stage_str + "\n 请按照格式直接给出指令，省略描述和解释。" 
        all_str = status_str + detected_str + status_str_new  +additional_str + stage_str + "\n 请按照格式直接给出指令，省略描述和解释。" 
        # 把文本发给大模型，获取返回来的文本
        if status_str_new=="test":
            # 说明是在单独调试这个
            # response_str = self.model_communication.communicate_with_model_debug(all_str)
            response_str = self.model_communication.communicate_with_model(all_str)
            # response_str = self.model_communication.communicate_with_model_single(all_str)
            # response_str = text_demo
        else:
            response_str = self.model_communication.communicate_with_model(all_str)

        # 把文本里面的命令提取出来
        commands = self.text_transfer.text_to_commands(response_str)

        # 把提取出来的命令发给agent，让它里面设定抽象状态啥的。
        self.redAgent.set_commands(commands) # 得专门给它定制一个发命令的才行，不然不行。

        self.add_fupan_info(self.timestep, commands, all_str, response_str)
        
        pass
    
    def run_one_step_shadow(self):
        # 这个对应env里面的shadow step。好像也没有什么需要执行的逻辑
        # 讲道理，这里面就干脆别搞跟大模型的互动了，不然要堵塞的，也不方便调试。
        # 但是显示可以搞。
        # 确切地说是有人类干预就和大模型互动，没有就别互动。
        # 从agent把态势拿出来
        self.status, self.detected_state= self.redAgent.get_status()

        # 把态势转成大模型能看懂的文本形式
        status_str = self.text_transfer.status_to_text(self.status)
        # 敌方的情况也得转，
        detected_str = self.text_transfer.detected_to_text(self.detected_state)
        # 再加一个子航给整的“人类指挥员注意力管理机制”，更新到dialog_box里面。
        zhuyili_str = self.text_transfer.turn_taishi_to_renhua(self.status, self.detected_state)

        # 把新的状态压入到解说的那一组线程里面去。
        self.shishi_TTS.add_status_list(status_str+detected_str)        

        # 检测是否人混的干预，有的话弄进去看
        flag_human_intervene, status_str_new = self.human_intervene_check(zhuyili_str + status_str + detected_str)
        
        # 增加态势阶段的提示。
        stage_str = self.stage_prompt.get_stage_prompt(self.timestep)

        if flag_human_intervene:
            # 那就是在shadow step里面执行人混的干预了。
            # 把文本发给大模型，获取返回来的文本
            if status_str_new=="test":
                # 说明是在单独调试这个
                response_str = "test"
            else:
                all_str = status_str + detected_str + status_str_new + stage_str + "请按照格式给出指令。"
                response_str = self.model_communication.communicate_with_model(all_str)

            # 把文本里面的命令提取出来
            commands = self.text_transfer.text_to_commands(response_str)

            # 把提取出来的命令发给agent，让它里面设定抽象状态啥的。
            self.redAgent.set_commands(commands) # 得专门给它定制一个发命令的才行，不然不行。            
            pass
        else:
            # 那就正常执行shadow step
            pass

        pass 

    def run_one_step_fupan(self):
        timestep = self.timestep # 先把当前的timestep获取出来。

        # 然后从复盘文件里面读。
        if timestep in self.fupan_pkl:
            # 那就是说明这一帧交互过了。
            # 那就来一遍
            all_str = self.fupan_pkl[timestep]["all_str"]
            command_list = self.fupan_pkl[timestep]["command"]
            response_str = self.fupan_pkl[timestep]["response_str"]

            # 然后执行一遍
            self.redAgent.set_commands(command_list)
        else:
            pass 

        # 下面这部分是读取态势并处理之后准备拿去另一个线程触发解说的
        
        # 从agent把态势拿出来
        self.status, self.detected_state= self.redAgent.get_status()

        # 把态势转成大模型能看懂的文本形式
        status_str = self.text_transfer.status_to_text(self.status)
        # 敌方的情况也得转，
        detected_str = self.text_transfer.detected_to_text(self.detected_state)
        # 再加一个子航给整的“人类指挥员注意力管理机制”，更新到dialog_box里面。
        zhuyili_str = self.text_transfer.turn_taishi_to_renhua(self.status, self.detected_state)

        self.status_jieshuo = status_str + detected_str + zhuyili_str
        # 原则上应该进一步优化，就是每次互动结束之后过几帧再开始存，或者直接就是收到了再开始存，鉴定为可以但没必要。
    
    def run_one_step_server(self):
        # 就每一步检测是不是更新，如果有更新就搞，没有就算了。和平台的交互是在这里面。
        # 从agent把态势拿出来
        self.status, self.detected_state= self.redAgent.get_status()
        # 还得分红蓝方，不然给过去乱的
        # status_red, detected_state_red = self.redAgent.get_status()
        status_blue, detected_state_blue = self.blueAgent.get_status()

        # 把态势转成大模型能看懂的文本形式
        status_str = self.text_transfer.status_to_text(self.status)
        status_str_blue = self.text_transfer.status_to_text(status_blue)
       

        detected_str = self.text_transfer.detected_to_text(self.detected_state)
        detected_str_blue = self.text_transfer.detected_to_text(detected_state_blue)
        # 再加一个子航给整的“人类指挥员注意力管理机制”，更新到dialog_box里面。
        zhuyili_str = self.text_transfer.turn_taishi_to_renhua(self.status, self.detected_state)        

        # # 然后检测，那边有没有回话。由于是检测，所以就得每一步都检测了。然后是不是执行动作就看有没有收到东西了
        # red_response_str, blue_response_str = self.socket_server.human_intervene_check()
        red_response_str, blue_response_str = self.human_intervene_check_server()

        # 增加态势阶段的提示。
        stage_str = self.stage_prompt.get_stage_prompt(self.timestep)
        # 理论上态势得分红蓝方，但是这个先放在 TODO 里面吧
        all_str = "当前态势："+status_str + detected_str  + stage_str + "\n 请按照格式给出指令。"     
        all_str_blue =  "当前态势："+status_str_blue + detected_str_blue  + stage_str + "\n 请按照格式给出指令。"     

        # 这些要socket发到client里面，然后检测有没有东西发回来。
        # 倒也不用每一步都发。调试的时候每一步都发可也
        if (self.timestep % 10 == 9) or True:
            all_str_list = [all_str, all_str_blue]
            self.dialog_box.get_status_str(all_str_list, self.timestep) # 这个又是一种方案
            print("run_one_step_server: status_str_list transfered ")

        print("run_one_step_server, stepping")
        time.sleep(0.5)
        if (len(red_response_str)>0) or (len(blue_response_str)>0):
            # or是只要有一边发了命令就走一步，and是两边都发了才走一步。感觉还是只要有就走比较合理。
            # 那就是说明是收到了东西了,那就走一步
            
            # 调试用的：这里停一下看看成色
            print("run_one_step_server, commands")
            # print(red_response_str)
            # time.sleep(1)

            # 把文本里面的命令提取出来。
            red_commands = self.text_transfer.text_to_commands(red_response_str)   
            blue_commands = self.text_transfer.text_to_commands(blue_response_str)  

            # 然后分别给到两个智能体。 # 把提取出来的命令发给agent，让它里面设定抽象状态啥的。
            self.redAgent.set_commands(red_commands) # 得专门给它定制一个发命令的才行，不然不行。
            self.blueAgent.set_commands(blue_commands) 

            self.add_fupan_info(self.timestep, (red_commands + blue_commands), all_str, (red_response_str+blue_response_str))
            print("run_one_step_server, commands, done")
        else:
            # 否则就不走这一步
            pass

        pass

    def run_one_step_client(self):
        # 联机的话和大模型的互动放在这里面了，把互动完事儿了的命令传回去就行了，刚好自带一个异步，岂不美哉
        
        # 先检测有没有收到态势，有就显示，然后再检测有没有人工干预，都有就触发和大模型的互动。
        # if self.socket_client.flag_new == True: # 不检测了，态势是空的就空的呗，无所谓。
        # 那就说明这一帧收到东西了。# 讲道理，不断刷标志位来触发还是不够保险，除非这边（main.py里面）的刷新频率远高于那边（socket里面）。比较理想的是用信号槽机制。
        # 还是统一弄到dialog box里面去比较好。
        # status_str_received = self.socket_client.receive_str() # 不能这么写，直接阻塞了，鉴定为拉
        # status_str_received = self.dialog_box.socket_client.status_str
        status_str_received = self.socket_client.status_str

        # 然后显示一下。以及交互，在这里面了
        flag_human_intervene, command_str = self.human_intervene_check(status_str_received)
            
        # if self.dialog_box.flag_order_renewed == True: # 这个失效了，原因不明。可能是什么线程不共享内存一类的？或者偷懒导致复制了
        if flag_human_intervene:
            # 那就是人下了命令。得分开，别跟人下命令那个耦合在一起。
            # 增加态势阶段的提示。
            stage_str = self.stage_prompt.get_stage_prompt(self.timestep)
            all_str = status_str_received + stage_str + command_str + "\n 请按照格式给出指令。" 
            # 把文本发给大模型，获取返回来的文本
            # 说明是在单独调试这个
            try:
                response_str = self.model_communication.communicate_with_model(all_str)
            except:
                # 这个说明大模型返回的API报错了
                print("寄，大模型API返回报错！")
                if self.role == "blue_player":
                    response_str = text_demo
                else:
                    response_str = text_demo_blue
            
            # response_str = '进攻指令：\n[move, obj_id=MainBattleTank_ZTZ100_0, x=100.138, y=13.6196],\n[move, obj_id=MainBattleTank_ZTZ100_1, x=100.138, y=13.6196],\n[move, obj_id=MainBattleTank_ZTZ100_2, x=100.138, y=13.6196],\n[move, obj_id=MainBattleTank_ZTZ100_3, x=100.138, y=13.6196],\n[move, obj_id=ArmoredTruck_ZTL100_0, x=100.138, y=13.6196],\n[move, obj_id=ArmoredTruck_ZTL100_1, x=100.138, y=13.6196],\n[move, obj_id=WheeledCmobatTruck_ZB100_0, x=100.138, y=13.6196],\n[move, obj_id=WheeledCmobatTruck_ZB100_1, x=100.138, y=13.6196],\n[move, obj_id=Howitzer_C100_0, x=100.138, y=13.6196],\n[move, obj_id=ShipboardCombat_plane0, x=100.137, y=13.644],\n[move, obj_id=RedCruiseMissile_0, x=100.116, y=13.643],\n[move, obj_id=RedCruiseMissile_1, x=100.164, y=13.658]'
            # response_str = "玩家指令：" + text_demo + str(random.randint(0,114514)) + "\n" # 加个随机数主要是为了防止字符串被识别成一样的
            response_str = "玩家指令：" + response_str  

            # 然后把交互好了的内容发到服务器那端去。
            self.socket_client.send_str(response_str)       

            # 本来应该是这里识别成命令再传过去，但是似乎会涉及一些重复的字符串转JSON，JSON转字符串之类的重复的事情，所以姑且先不慌在客户端解析，反正也没多少计算量。        
        pass
   
    def run_one_step_model3(self,**kargs):
        # 这个是服务于那个辅助决策的模块3的。其实逻辑可以先简单一点。但是这么写的话留出了之后扩展的可能性。
        
        # 从agent把态势拿出来
        self.status, self.detected_state= self.redAgent.get_status()

        # 然后就可以直接快进到“模块三”了。初始化是在外面做，这里只调用one step那个
        plan_input = kargs["plan_interface"] 

        commands = plan_input.get_action_one_step(self.timestep,self.status)

        # 把提取出来的命令发给agent，让它里面设定抽象状态啥的。
        self.redAgent.set_commands(commands) # 得专门给它定制一个发命令的才行，不然不行。

        all_str = "no all_str, this is " + self.role
        response_str = "no response_str, this is " + self.role

        self.add_fupan_info(self.timestep, commands, all_str, response_str)    

        # 还得来，加一系列给前端拿过去显示的东西。
        if self.communicator != None:
            # 那就是初始化过了往展示用可视化前端传东西的了
            if self.timestep == 0:
                # 那就是第一帧，得把态势传过去。
                for i in range(10):
                    # 分包，分10次传过去。
                    commands_dict = plan_input.get_action_for_liancan(self.timestep,self.status,index=i)
                    # response_str = self.communicator.send_response(str(commands_dict))
                    response_str = self.communicator.send_dict(commands_dict)
                    # 储存到文件里面，看看成色。这个是debug的时候用。
                    # with open("auto_test/response_str"+str(i)+".txt", "a") as f:
                    #     f.write(response_str)
            else:
                # str_dict = {}
                # str_dict["当前帧数"] = self.timestep
                # str_dict["当前指令"] = str(commands)
                # 这都是随便传一点儿过去，等到真搞的时候得定制接口
                keys_str = "" 
                for keys in commands:
                    keys_str = keys_str + ", "+str(keys)
                str_all = "测试中，当前帧数：" + str(self.timestep) + "，当前指令："+keys_str
                print(str_all)

                # commands_dict = {}
                # commands_dict[str(self.timestep)] = [] 
                # response_str = self.communicator.send_dict(commands_dict)
                # self.communicator.send_response(str(str_all))
                # self.communicator.send_response(str(self.timestep))
                response_str = self.communicator.send_dict(self.timestep)

                pass

    def get_status_dixing(self,status):
        # 这个想要实现的是把每一个装备的当前地形都拿出来，然后再塞回去status里面。反正多点儿没有坏处就是了。
        print("unfinished yet: get_status_dixing")
        pass

    def human_intervene_check(self, status_str):
        # 2024年6月4日09:34:20这个看起来不对，得重新写一下才对。
        # 输入输出怎么做还两说呢，整个窗口？然后用信号槽机制实现人输入的这个异步，可行。
        command_str = "test"

        print("debug: human_intervene_check reached" + str(self.dialog_box.flag_order_renewed))
        time.sleep(0.5)
        # 检测窗口是不是被下过命令，是就读出来，重置标志位，不是就再说
        if self.role == "offline":
            panju = self.dialog_box.flag_order_renewed
        else:
            # 这里再加一层检测
            if "dialog_box_model" in self.config:
                if self.config["dialog_box_model"] == "QtC++":
                    # 那就是和雪楠哥他们给弄的那个窗口去对，那就不是从self.socket_client去读了，得是从self.dialog_box去读。
                    panju = self.dialog_box.flag_order_renewed
                else:
                    panju = self.socket_client.flag_human_interact
            else:
                panju = self.socket_client.flag_human_interact
                    
        # if self.dialog_box.flag_order_renewed: 
        if panju == True:
            
            # 把人类的命令读出来
            # command_str = "现在我的具体意图是：" + self.dialog_box.order_now # 这个更新的有问题，但是来不及排查为啥了，只好屎山化了。
            try:
                command_str = "现在我的具体意图是：" + self.dialog_box.env.received_str
            except:
                command_str = "现在我的具体意图是：" + self.dialog_box.order_now
            self.human_order = command_str

            self.flag_human_interact = True
            # 外面不能直接用self.dialog_box.flag_order_renewed，因为服从于界面的逻辑，这个变量得重置
            # 刷新一下窗口并重置标志位。考虑一下是不是需要延时。
            
            print("debug: human_intervene_check human_order "+self.human_order)
            # time.sleep(0.5)

            self.dialog_box.reset_all(0.02)
        else:
            # 那就是窗口那头没有下过命令，那就先不管了
            command_str = self.human_order
            pass

        # 然后还得把接收到的态势显示出来才行
        self.dialog_box.get_status_str(status_str,self.timestep)

        # 完事儿了把标志位改成false
        if self.role == "offline":
            pass
        else:
            self.socket_client.flag_human_interact = False

        return self.flag_human_interact , command_str

    def human_intervene_check_server(self):
        # 这个是有说法的了，检测两个server看是不是收到了那边传来的东西。
        # 异步的存在时间差的问题，那边收到了之后只保留1帧，所以得好好设计时间差，甚至直接不要时间差了
        red_response_str_new, blue_response_str_new = self.dialog_box.socket_server.human_intervene_check()
        print("human_intervene_check_server")
        if ("开始推演" in red_response_str_new) or ("开始推演" in blue_response_str_new):
            # 那就开呗。然而写在这里应该是开不了的。
            # 开始逻辑得改改，上来先把循环开了，然后加个标志位。
            self.config["flag_server_waiting"] = False
            print("human_intervene_check_server: 开始推演")
            pass
        if ("结束推演" in red_response_str_new) or ("结束推演" in blue_response_str_new):
            # 那就结束，在这里写至少是能结束的。
            self.terminate()
            print("human_intervene_check_server: 结束推演")
            self.config["flag_server_waiting"] = True # 按理说这个没啥用，但是保险起见
            pass

        if red_response_str_new != self.red_response_str:
            # 那就是命令被更新过了。
            red_response_str_return = red_response_str_new
            self.red_response_str = red_response_str_new
        else:
            # 那就是命令没有被更新，那就无事发生
            red_response_str_return = ""
        
        if blue_response_str_new != self.blue_response_str:
            blue_response_str_return = blue_response_str_new
            self.blue_response_str = blue_response_str_new    
        else:
            blue_response_str_return = ""           

        # 算了，这里再做一个好了，来个检测有没有更新的机制。如果有更新，就来新的，没有更新，就来空的，而不要重复的一直刷，没意思。
        return red_response_str_return, blue_response_str_return
    
    def main_loop_wrap(self,**kargs):
        # 这个是复用main_loop，实现一个"监听等待客户端都准备完毕”
        while True:
            if self.config["flag_server_waiting"] == True:
                # 那就说明是在等着.检测的功能集成到这个里面去了。
                flag_human_intervene, status_str_new = self.human_intervene_check_server()
                print("command_processor as server: waiting")
                time.sleep(1.14514)
                # if self.config["flag_server_waiting"] == False:
                #     break
            elif self.config["flag_server_waiting"] == False:
                # 那就是无事发生
                self.main_loop()


    def main_loop(self,**kargs):
        # 这个是类似之前的auto_run的东西，跟平台那边要保持交互的。
        self.timestep = 0 # 每个episode的步数
        log_file = auto_save_file_name(log_folder=r'auto_test')
        
        if "fupan_name" in kargs:
            # 说明是复盘模式
            fupan_name = kargs["fupan_name"]
        else:
            fupan_name = ""
        
        if "role" in kargs:
            # 说明是复盘模式
            self.role = kargs["role"]
        else:
            self.role = "offline"
        
        # 训练环境初始化，并返回红蓝方舰船编号
        print("begin resetting")
        unit_ids_dict = self.env.Reset()
        unit_ids_dict = json.loads(unit_ids_dict)

        redAgent = self.redAgent
        blueAgent = self.blueAgent

        # 和去年的不同，这里要初始化global和local
        redAgent.init_agent(unit_ids_dict['RedShipID'])
        blueAgent.init_agent(unit_ids_dict['BlueShipID'])     
        # 红蓝方智能体全局变量初始化
        redAgent.reset()
        blueAgent.reset()
        print("finish resetting")
        s= []
        u = []
        s_next = []

        act = []
        act += redAgent.deploy(unit_ids_dict['RedShipID'])
        act += blueAgent.deploy(unit_ids_dict['BlueShipID'])
        action = {"Action": act}
        print("action ", action)
        self.env.Step(Action = action)

        # 获取红蓝方态势信息
        cur_redState, cur_blueState = get_states(self.env)
        tips = '\n start main loop: \n'
        cur_redState_str, start_redState_list = auto_state_filter(cur_redState)
        cur_blueState_str, start_blueState_list = auto_state_filter(cur_blueState)
        auto_save(log_file, tips, cur_redState_str, cur_blueState_str)

        # 开搞之前存一下本次测试的配置，xxh0920
        strbuffer = "\n\n现在是" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + "，开始执行测试。\n 测试配置：\n"

        auto_save_overall(strbuffer, log_file=self.log_file)

        # # 先和大模型互动一波，讲讲规则什么的。
        # self.the_embrace()

        # 如果是复盘就按照复盘模式跑，如果不是就按照正常的模式跑
        if fupan_name != "":
            # 先读取复盘文件
            self.load_fupan_info(fupan_name)
            # 然后改标志位
            self.flag_fupan = True
        else:
            # 正常模式
            self.flag_fupan = False
            pass

        self.flag_finished = False # 这个是用来给其他线程看的。
        # 智能体与环境交互生成训练数据
        while True:
            
            # 调试的时候，这里每一步加一个比较大的时间延迟，让它别太快推完。
            time.sleep(0.5)
            print("debug, time delay in main_loop.")

            self.env.SetRender(True) # 训练界面可视化：False --> 关闭
            act = []
            action = {"Action": act}
            self.flag_human_interact = False

            # 红蓝方智能体产生动作
            act += redAgent.step(cur_redState) # 这么玩要能成立，step里面得是空的，抽象状态都在run_one_step里面根据各人的命令来改。
            act += blueAgent.step(cur_blueState)  # 所以抽象状态改了之后得到下一步才会真正生效，正常问题不大应该。
            if self.flag_fupan == False:
                if self.role == "offline":
                    # 这个就是无事发生，和以前的一样正常跑
                    if (self.timestep % 300 == 0) and (self.flag_regular_interacte==True):
                        additional_str = ""
                        if self.timestep == 0:
                            # additional_str = self.the_embrace()            
                            if self.LLM_model =="qianfan":
                                # 只要思想肯滑坡，办法总比困难多。
                                additional_str = self.the_embrace()            
                            pass 
                        else:
                            pass
                            # additional_str = ""
                        # # 由于百度限制了长度，所以每次都得来一遍初拥了（悲
                        # additional_str = self.the_embrace()
                        self.run_one_step(additional_str=additional_str)
                    else:
                        self.run_one_step_shadow()
                elif self.role =="server":
                    # 这个就是本线程为服务器，不再取模了，直接拉满。
                    self.run_one_step_server()
                    # 这里还得增加一个逻辑，就是服务器端直接给它跑着，等待用户命令。
                elif (self.role == "red_player") or (self.role == "blue_player"):
                    self.run_one_step_client()
                elif self.role == "model3":
                    # 这个是后面的辅助决策用来和其他部分联系的。
                    self.run_one_step_model3(**kargs) # 直接把那个interface作为引用传进去好了，反正也没有什么特别大的所谓。
            else:
                self.run_one_step_fupan()
            
            # 其实只有非复盘状态下这个才有意义，否则0除以0了
            if (self.timestep % 100 == 0) and (self.timestep>500) and (self.flag_fupan == False):
                # 每100步就看看成色
                self.model_communication.get_tokens()
                self.text_transfer.get_num_commands()

            self.env.Step(Action = action)
            next_redState, next_blueState = get_states(self.env)

            # 这里来一段，识别一下这一帧是否有装备毁伤。
            cur_redState_str, cur_redState_list = auto_state_filter(cur_redState)
            cur_blueState_str, cur_blueState_list = auto_state_filter(cur_blueState)
            next_redState_str, next_redState_list = auto_state_filter(next_redState)
            next_blueState_str, next_blueState_list = auto_state_filter(next_blueState)

            cur_result = json.loads(self.env.GetCurrentResult())
            redState_diff_str, redState_diff_num = auto_state_compare2(cur_redState_list, next_redState_list)
            blueState_diff_str, blueState_diff_num = auto_state_compare2(cur_blueState_list, next_blueState_list)
            if blueState_diff_num>0:
                # 说明在这一帧有蓝方装备被摧毁，值得写一条日志。
                strbuffer = "在第"+str(self.timestep)+"帧有"+str(blueState_diff_num)+"个目标被摧毁，是" + blueState_diff_str
                auto_save_overall(strbuffer, log_file=self.log_file)
            # 红方就先不写了，不然全是导弹子弹被摧毁，乱的一B

            # 记录每一轮运行的日志。面向过程编程还是难受，应该一开始就别偷懒。
            tips = '\n timestep now: ' + str(self.timestep) + '\n'
            tips = tips + auto_state_compare(cur_blueState_list, start_blueState_list)
            auto_save(self.log_file, tips, cur_redState_str, cur_blueState_str)
            self.timestep += 1

            cur_redState = next_redState
            cur_blueState = next_blueState

            # 一个对战回合结束进入下一回合
            if self.timestep > self.max_episode_len:
                # 获取当前分数
                cur_result = json.loads(self.env.GetCurrentResult())
                try:
                    blueScore_str = "blueScore: " + str(cur_result["blueScore"])
                    redScore_str = "redScore: " + str(cur_result["redScore"])
                    print(redScore_str)
                    print(blueScore_str)
                    tips = '\n get result: timestep =' + str(self.timestep) + '\n'
                    # auto_save(log_file, tips, cur_result)
                    auto_save(self.log_file, tips, redScore_str, blueScore_str)
                    # result = env.Terminal()
                    auto_save_overall(blueScore_str + '\n' + redScore_str, log_file=self.log_file)
                except:
                    print("G!,返回值里面并不包含分数，该不会还要自己从态势去算吧，下次一定。")
                self.flag_finished = True # 这个是用来给其他线程看的。
                break        
        
        if self.flag_fupan == False:
            # 如果不是复盘状态，那就存一下
            self.save_fupan_info()
        pass 
   
    def main_loop_client(self):
        # 还是不行，还是得定制一个专门用于客户端通信的。搅合在一起是不理智的。
        self.flag_finished = False # 这个是用来给其他线程看的。
        
        # 智能体与环境交互生成训练数据
        while True:
            # 这里面就不限步数了，因为这边的步数和平台那里的肯定是不同步的。
            self.flag_human_interact = False
            time.sleep(0.01)        
            if (self.role == "red_player") or (self.role == "blue_player"):
                self.run_one_step_client()    
                
    def the_embrace(self):
        # 先和大模型互动一波，讲讲规则什么的。这个也是从run_one_step衍生出来的。
        all_str = self.text_transfer.get_initial_prompt()
        all_str += self.text_transfer.get_order_guize()

        all_str += "准备好了吗？"

        # response_str = self.model_communication.communicate_with_model(all_str)
        # print(response_str)
        
        # # 把文本里面的命令提取出来
        # commands = self.text_transfer.text_to_commands(response_str)

        # # 把提取出来的命令发给agent，让它里面设定抽象状态啥的。
        # self.redAgent.set_commands(commands) # 得专门给它定制一个发命令的才行，不然不行。
        return all_str
    
    def the_embrace_jieshuo(self):
        all_str = "请作为解说员，解说一场兵棋推演比赛，尽量讲清楚双方作战过程和行动逻辑，准备好了吗？"
        return all_str

    def jieshuo_mul_thread(self):
        # 这个试图用来实现游戏解说。其实和态势认知几乎是一回事。
        # 开两个线程，一个用来跑复盘，再一个用来和大模型互动。
        self.status_jieshuo = ""
        thread1 = threading.Thread(target=self.main_loop,kwargs={"fupan_name": r"auto_test_log0"})
        thread2 = threading.Thread(target=self.jieshuo_single)

        # 然后就启动线程呗
        thread1.start()
        thread2.start()
        # 然后就等待线程结束呗
        thread1.join()
        thread2.join()
        # 然后就返回结果呗
        print("回合结束，鉴定为：解说demo好使")
        return self.status_jieshuo

    def jieshuo_single(self):
        # 不传参数了，从共享内存里直接读出类的成员变量，可也。
        all_str = self.status_jieshuo

        # 这么简单？这么玩的话岂不是直接就可以开始来进行解说了？
        for i in range(114):
            response_str = self.model_communication.communicate_with_model(all_str)
            print(response_str)
            if self.flag_finished == True:
                break # 那边要是跑完了，这边就直接退了
    
    def turn_on_CraftGame(self,**kargs):
        # 这个是直接启动推演平台。每次手开开始比较傻逼的。
        # cmd_order1 = r"D: & cd D:/ruanjian_M/2024LDJS_1219/2025LDJS_0224_LLM/exe/exe & CraftGameV1.exe"
        self.exe_thread_list = [] 
        if "cmd_order" in kargs:
            cmd_order1 = kargs["cmd_order"]
        else:
            cmd_order1 = r"D: & cd D:/ruanjian_M/2024LDJS_1219/2025LDJS_0224_LLM/exe/exe & CraftGameV1.exe"

        if "thread_num" in kargs:
            self.thread_num = kargs["thread_num"]
        else:
            self.thread_num = 1 # 这个是线程数量，默认是1

        for i in range(self.thread_num):
            # 先初始化一堆线程，然后在里面给它润起来，然后再说别的。
            thread_single = threading.Thread(target=self.turn_on_CraftGame_single,args=(cmd_order1,))
            self.exe_thread_list.append(thread_single)
        # 然后全部启动一遍然后就摆了
        for i in range(self.thread_num):
            thread_single = self.exe_thread_list[i]
            thread_single.start()    

        # 来点儿延时，不然开不起来万一
        time.sleep(1.14*5.14)


        print("这会儿应该启动了一堆平台了")
        pass
    
    def turn_on_CraftGame_single(self,order:str):
        # 这个是用来开多线程的，防止给我主线程阻塞了。
        cmd_order1 = order
        os.system(cmd_order1) # 还是这个靠谱，subprocess.Popen会报权限问题                
    
    def exit_all_exe(self):
        # 按说这个应该写在析构函数里面，别在外面调用才是比较好的。但是开着多线程好像析构不了，算了不管了。
        # for i in range(self.thread_num):
        #     thread_single = self.exe_thread_list[i]
        cmd_kill = "taskkill /IM CraftGameV1.exe -F"
        os.system(cmd_kill) # 还是这个靠谱，subprocess.Popen会报权限问题        
        print("这会儿平台应该关完了")  
        return True
if __name__ == "__main__":
    # # 这个是总的测试的了
    flag = 7
    shishi_debug = MyWidget_debug() # 无人干预
    # shishi_debug = MyWidget_debug2() # 模拟有人干预
    
    if flag == 0:
        # 这个是单跑这个不跑dialog box，拟似人混，启动！ # 20241012里面还加持了大模型解说。
        shishi = command_processor(shishi_debug)
        shishi.main_loop()
    elif flag == 1:
        # 这个是加载并运行特定复盘文件。
        shishi = command_processor(shishi_debug)
        shishi.main_loop(fupan_name=r"auto_test_log0")
    elif flag == 2:
        # 这个是加载特定的AI，然后再来运行。
        shishi = command_processor(shishi_debug)
        shishi.get_agent_out(role="blue",location=r"C:\Users\42418\Desktop\2024ldjs\EnglishMulu\Team\LGD.DK&NUIST")
        shishi.main_loop()
    elif flag == 4:
        # 这个是加载并运行特定的复盘，然后解说比赛的demo
        shishi = command_processor(shishi_debug,Comm_type ="jieshuo")
        shishi.jieshuo_mul_thread()
    elif flag == 5:
        # # 这个是开起来当服务器的，跑在需要跟平台交互的电脑上。
        # config = {"red_ip":"192.168.1.140", "red_port": "20001",
        #           "blue_ip": "192.168.1.140", "blue_port": "20002" }
        # # shishi_debug = MyWidget_debug(role="server",config=config) # 无人干预
        # shishi = command_processor(shishi_debug,role="server",config=config)
        # shishi.run()
        # # 由于dialog box和command_processor的相互引用关系，理智的做法是改在dialogbox_sserver里面，而不是直接开这个。
        # # 然后相应的client进程得从dialog_box里面去跑，真是一点也不可喜，一点也不可贺啊，越搞越乱了属于是。
        pass
    elif flag == 6:
        # 这个是一个简化的模块3，用于先连起来。
        shishi_interface = plan_interface()
        plan_location_list = [] 
        plan_location_list.append(r"D:/EnglishMulu/test_decision/auto_test/新的/jieguo0.pkl")
        # plan_location_list.append(r"D:/EnglishMulu/test_decision/auto_test/jieguo1.pkl")
        # plan_location_list.append(r"D:/EnglishMulu/test_decision/auto_test/jieguo2.pkl")
        shishi_interface.load_plans(plan_location_list) 
        shishi_interface.set_plan(0) # 设定一下准备用哪个。       

        # 这个是单跑这个不跑dialog box，拟似人混，启动！
        shishi = command_processor(shishi_debug,flag_auto_CraftGame=False)
        shishi.main_loop(role ="model3", plan_interface = shishi_interface)
    elif flag == 7:
        # 测试直接在python里起动平台，就不用每次手点了。
        shishi = command_processor(shishi_debug,flag_auto_CraftGame=True)
        # shishi.turn_on_CraftGame()
        print("测试直接在python里起动平台，就不用每次手点了。")
        time.sleep(1.14*5.14)
        shishi.exit_all_exe()  
    else:
        print("undefined running model yet. ")