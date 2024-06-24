# 这个是主函数，到时候就运行这个就完事了。
from agent_guize.agent import Agent
from agent_guize.enemy_AI.blue_agent import BlueAgent
from agent_guize.me_AI.red_agent import RedAgent
from agent_guize.Env import Env,Env_demo
from agent_guize.tools import get_states, auto_state_filter, auto_state_compare2 , auto_save_overall, auto_save, auto_save_file_name, auto_state_compare
from text_transfer.text_transfer import text_transfer, text_demo
from text_transfer.stage_prompt import StagePrompt
from model_communication.model_communication import model_communication
from model_communication.model_comm_langchain import ModelCommLangchain
from dialog_box.dialog_box_debug import *

import json
import time 
import argparse
import sys,os,pickle
from importlib import import_module

from PySide6 import QtCore, QtWidgets, QtGui

class command_processor(QtCore.QThread):
    
    def __init__(self,dialog_box):
        super().__init__()
        self.runnig_location = r"auto_test"
        self.log_file = r'overall_result.txt'

        self.args = self.__init_net()
        self.__init_env()
        self.__init_agent()

        self.text_transfer = text_transfer()
        self.stage_prompt = StagePrompt()
        self.LLM_model = "qianfan" # 这里可以改，默认是qianfan,还有智谱啥的
        # self.model_communication = model_communication()
        # self.model_communication = ModelCommLangchain(model_name="zhipu")
        self.model_communication = ModelCommLangchain(model_name=self.LLM_model)
        # self.__init_dialog_box()
        self.dialog_box = dialog_box
        self.__init_env()
        self.status= {} # 这个是我方的
        self.detected_state = {} # 这个是敌方的
        self.timestep = 0 
        self.flag_human_interact = False #这个用来标志当前时间步是否引入人类交互。
        self.human_order = "" # 这个用来常态化地存人类交互指令，以防人类意图只出现一帧就被盖了

        # 搞一个用来存复盘的东西。
        self.fupan_pkl = {} # {timestep: {"command":command_list, "all_str":all_str, "response_str":response_str} }
        self.flag_fupan = False # 用来标记当前是否在复盘。
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
        parser.add_argument("--max-episode-len", type=int, default=3000, help="maximum episode length")
        net_args = parser.parse_args()
        return net_args

    def __init_agent(self):
        # 这里面应该不要含有需要给后端发东西的内容，以便调试。
        self.redAgent = RedAgent()
        self.blueAgent = BlueAgent()
        self.red_deploy_location = self.runnig_location + r'\guize\reddeploy'
        self.blue_deploy_location = self.runnig_location + r'\guize\bluedeploy'
        # self.redAgent.set_deploy_folder(self.red_deploy_location)
        # self.blueAgent.set_deploy_folder(self.blue_deploy_location)
    def get_agent_out(self,role="blue",location = r""):
        # 这个是搞一个方便地装载外部agent的接口。从去年劳动竞赛的craft manager的基础上开发出来的。
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
                print("command_processor is running")
                self.main_loop()
            else:
                print("command_processor is off")
                pass

    def run_one_step(self,additional_str=""):
        # 从agent把态势拿出来
        self.status, self.detected_state= self.redAgent.get_status()

        # 把态势转成大模型能看懂的文本形式
        status_str = self.text_transfer.status_to_text(self.status)
        detected_str = self.text_transfer.detected_to_text(self.detected_state)
        # 再加一个子航给整的“人类指挥员注意力管理机制”，更新到dialog_box里面。
        zhuyili_str = self.text_transfer.turn_taishi_to_renhua(self.status, self.detected_state)        

        # 检测是否人混的干预，有的话也弄进去
        flag_human_intervene, status_str_new = self.human_intervene_check(zhuyili_str + status_str + detected_str)

        # 增加态势阶段的提示。
        stage_str = self.stage_prompt.get_stage_prompt(self.timestep)
        all_str = status_str + detected_str + status_str_new + stage_str +additional_str + "\n 请按照格式给出指令。" 
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

    def human_intervene_check(self, status_str):
        # 2024年6月4日09:34:20这个看起来不对，得重新写一下才对。
        # 输入输出怎么做还两说呢，整个窗口？然后用信号槽机制实现人输入的这个异步，可行。
        command_str = "test"

        print("debug: human_intervene_check reached")
        print(self.dialog_box.flag_order_renewed)
        time.sleep(0.1)
        # 检测窗口是不是被下过命令，是就读出来，重置标志位，不是就再说
        if self.dialog_box.flag_order_renewed:
            
            # 把人类的命令读出来
            command_str = "现在我的具体意图是：" + self.dialog_box.order_now
            self.human_order = command_str

            self.flag_human_interact = True
            # 外面不能直接用self.dialog_box.flag_order_renewed，因为服从于界面的逻辑，这个变量得重置
            # 刷新一下窗口并重置标志位。考虑一下是不是需要延时。
            self.dialog_box.reset_all(0.02)
        else:
            # 那就是窗口那头没有下过命令，那就先不管了
            command_str = self.human_order
            pass

        # 然后还得把接收到的态势显示出来才行
        self.dialog_box.get_status_str(status_str,self.timestep)

        return self.flag_human_interact , command_str
    
    def main_loop(self,fupan_name=""):
        # 这个是类似之前的auto_run的东西，跟平台那边要保持交互的。
        self.timestep = 0 # 每个episode的步数
        log_file = auto_save_file_name(log_folder=r'auto_test')
        
        # 训练环境初始化，并返回红蓝方舰船编号
        print("begin resetting")
        shipIDlist = self.env.Reset()
        shipIDlist = json.loads(shipIDlist)

        redAgent = self.redAgent
        blueAgent = self.blueAgent

        # 红蓝方智能体全局变量初始化
        redAgent.reset()
        blueAgent.reset()
        print("finish resetting")
        s= []
        u = []
        s_next = []

        act = []
        # print("shipIDList ", shipIDlist)
        act += redAgent.deploy(shipIDlist['RedShipID'])
        act += blueAgent.deploy(shipIDlist['BlueShipID'])
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


        # 智能体与环境交互生成训练数据
        while True:
            self.env.SetRender(True) # 训练界面可视化：False --> 关闭
            act = []
            action = {"Action": act}
            self.flag_human_interact = False

            # 红蓝方智能体产生动作
            act += redAgent.step(cur_redState) # 原则上这一层应该是不加东西的
            if self.flag_fupan == False:
                if self.timestep % 300 == 0:
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
            else:
                self.run_one_step_fupan()
            
            # 其实只有非复盘状态下这个才有意义，否则0除以0了
            if (self.timestep % 100 == 0) and (self.timestep>500) and (self.flag_fupan == False):
                # 每100步就看看成色
                self.model_communication.get_tokens()
                self.text_transfer.get_num_commands()

            # act += redAgent.step(cur_redState)
            act += blueAgent.step(cur_blueState)

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
                blueScore_str = "blueScore: " + str(cur_result["blueScore"])
                redScore_str = "redScore: " + str(cur_result["redScore"])
                print(redScore_str)
                print(blueScore_str)
                tips = '\n get result: timestep =' + str(self.timestep) + '\n'
                # auto_save(log_file, tips, cur_result)
                auto_save(self.log_file, tips, redScore_str, blueScore_str)
                # result = env.Terminal()
                auto_save_overall(blueScore_str + '\n' + redScore_str, log_file=self.log_file)
                break        
        
        if self.flag_fupan == False:
            # 如果不是复盘状态，那就存一下
            self.save_fupan_info()
        pass 

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
    
if __name__ == "__main__":
    # # 这个是总的测试的了
    flag = 2
    # shishi_debug = MyWidget_debug() # 无人干预
    shishi_debug = MyWidget_debug2() # 模拟有人干预
    shishi = command_processor(shishi_debug)
    if flag == 0:
        # 这个是单跑这个不跑dialog box，拟似人混，启动！
        shishi.main_loop()
    elif flag == 1:
        # 这个是加载并运行特定复盘文件。
        shishi.main_loop(fupan_name=r"auto_test_log0")
    elif flag == 2:
        # 这个是加载特定的AI，然后再来运行。
        shishi.get_agent_out(role="blue",location=r"C:\Users\42418\Desktop\2024ldjs\EnglishMulu\Team\LGD.DK&NUIST")
        shishi.main_loop()