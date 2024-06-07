# 这个是主函数，到时候就运行这个就完事了。
from agent_guize.agent import Agent
from agent_guize.enemy_AI.blue_agent import BlueAgent
from agent_guize.me_AI.red_agent import RedAgent
from agent_guize.Env import Env,Env_demo
from agent_guize.tools import get_states, auto_state_filter, auto_state_compare2 , auto_save_overall, auto_save, auto_save_file_name, auto_state_compare
from text_transfer.text_transfer import text_transfer
from model_communication.model_communication import model_communication

import json
import time 
import argparse
import sys 

from PySide6 import QtCore, QtWidgets, QtGui

class command_processor(QtCore.QThread):
    
    def __init__(self,dialog_box):
        super().__init__()
        self.runnig_location = r"C:\Users\42418\Desktop\2024ldjs\EnglishMulu\auto_test"
        self.log_file = r'C:\Users\42418\Desktop\2024ldjs\EnglishMulu\overall_result.txt'

        self.args = self.__init_net()
        self.__init_env()
        self.__init_agent()

        self.text_transfer = text_transfer()
        self.model_communication = model_communication()
        # self.__init_dialog_box()
        self.dialog_box = dialog_box
        self.__init_env()
        self.status= {} # 这个是我方的
        self.detected_state = {} # 这个是敌方的
        self.timestep = 0 
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

        # 检测是否人混的干预，有的话也弄进去
        flag_human_intervene, status_str_new = self.human_intervene_check(status_str + detected_str)
        
        all_str = additional_str + status_str + detected_str + status_str_new + "，请按照格式给出指令。" 
        # 把文本发给大模型，获取返回来的文本
        if status_str_new=="test":
            # 说明是在单独调试这个
            # response_str = self.model_communication.communicate_with_model_debug(all_str)
            response_str = self.model_communication.communicate_with_model(all_str)
        else:
            response_str = self.model_communication.communicate_with_model(all_str)

        # 把文本里面的命令提取出来
        commands = self.text_transfer.text_to_commands(response_str)

        # 把提取出来的命令发给agent，让它里面设定抽象状态啥的。
        self.redAgent.set_commands(commands) # 得专门给它定制一个发命令的才行，不然不行。
        
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

        # 检测是否人混的干预，有的话弄进去看
        flag_human_intervene, status_str_new = self.human_intervene_check(status_str + detected_str)
        
        
        if flag_human_intervene:
            # 那就是在shadow step里面执行人混的干预了。
            # 把文本发给大模型，获取返回来的文本
            if status_str_new=="test":
                # 说明是在单独调试这个
                response_str = "test"
            else:
                all_str = status_str + detected_str + status_str_new + "，请按照格式给出指令。"
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
        command_str = "none"
        
        # 检测窗口是不是被下过命令，是就读出来，重置标志位，不是就再说
        if self.dialog_box.flag_order_renewed:
            
            # 把人类的命令读出来
            command_str = self.dialog_box.order_now
            
            # 刷新一下窗口并重置标志位。考虑一下是不是需要延时。
            self.dialog_box.reset_all(0.02)
        else:
            # 那就是窗口那头没有下过命令，那就先不管了
            pass

        # 然后还得把接收到的态势显示出来才行
        self.dialog_box.get_status_str(status_str,self.timestep)

        return self.dialog_box.flag_order_renewed, command_str
    
    def main_loop(self):
        # 这个是类似之前的auto_run的东西，跟平台那边要保持交互的。
        self.timestep = 0 # 每个episode的步数
        log_file = auto_save_file_name(log_folder=r'C:\Users\42418\Desktop\2024ldjs\EnglishMulu\auto_test')
        
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

        # 智能体与环境交互生成训练数据
        while True:
            self.env.SetRender(True) # 训练界面可视化：False --> 关闭
            act = []
            action = {"Action": act}
            # 红蓝方智能体产生动作
            act += redAgent.step(cur_redState) # 原则上这一层应该是不加东西的
            if self.timestep % 30 == 0:
                if self.timestep == 0:
                    additional_str = self.the_embrace()
                else:
                    additional_str = ""
                self.run_one_step(additional_str=additional_str)
            else:
                self.run_one_step_shadow()

            act += redAgent.step(cur_redState)
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


class MyWidget_debug:
    def __init__(self):
        # 这个是用来隔离一下，单独debug一下main_loop的
        self.timestep = 0
        self.flag_order_renewed = True
        self.order_now = "test"
    
    def get_status_str(self,status_str, timestep):
        # 获取当前状态
        pass

    def reset_all(self, canshu=0):
        # 重置所有状态
        pass
    
if __name__ == "__main__":
    # # 这个是总的测试的了
    shishi_debug = MyWidget_debug()
    shishi = command_processor(shishi_debug)
    shishi.main_loop()