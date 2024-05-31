# 这个是主函数，到时候就运行这个就完事了。
from agent_guize.agent import Agent
from agent_guize.Env import Env,Env_demo
from agent_guize.tools import get_states, auto_state_filter, auto_state_compare2 , auto_save_overall, auto_save, auto_save_file_name, auto_state_compare
from text_transfer.text_transfer import text_transfer
from model_communication.model_communication import model_communication
from dialog_box import MyWidget

import json
import time 

from PySide6 import QtCore, QtWidgets, QtGui

class command_processor:
    
    def __init__(self):
        # self.agent = agent()
        self.redAgent = Agent("Red")
        self.blueAgent = Agent("Blue")

        self.text_transfer = text_transfer()
        self.model_communication = model_communication()
        self.__init_dialog_box()
        self.__init_env()
        self.status= {}

        self.log_file = r'C:\Users\42418\Desktop\2024ldjs\EnglishMulu\overall_result.txt'
        pass
    
    def __init_dialog_box(self):
        # 初始化对话框
        app = QtWidgets.QApplication([])
        self.dialog_box = MyWidget()
        self.dialog_box.resize(800, 300)
        self.dialog_box.show()
        pass
    
    def __init_env(self):
        self.max_episode_len = 1145 
        # self.env = Env(self.max_episode_len)
        self.env = Env_demo(114, 514)


    def run_one_step(self):
        # 从agent把态势拿出来
        self.status= self.redAgent.get_status()

        # 把态势转成大模型能看懂的文本形式
        status_str = self.text_transfer.status_to_text(self.status)

        # 检测是否人混的干预，有的话也弄进去
        flag_human_intervene, status_str_new = self.human_intervene_check(status_str_new)

        # 把文本发给大模型，获取返回来的文本
        response_str = self.model_communication.communicate_with_model(status_str_new)

        # 把文本里面的命令提取出来
        commands = self.text_transfer.text_to_commands(response_str)

        # 把提取出来的命令发给agent，让它里面设定抽象状态啥的。
        self.redAgent.set_commands(commands) # 得专门给它定制一个发命令的才行，不然不行。
        
        pass
    
    def run_one_step_shadow(self):
        # 这个对应env里面的shadow step。好像也没有什么需要执行的逻辑

        # 检测是否人混的干预，有的话弄进去看
        flag_human_intervene, status_str_new = self.human_intervene_check(status_str_new)

        if flag_human_intervene:
            # 那就是在shadow step里面执行人混的干预了。
            # 把文本发给大模型，获取返回来的文本
            response_str = self.model_communication.interact_with_LLM(status_str_new)

            # 把文本里面的命令提取出来
            commands = self.text_transfer.text_to_commands(response_str)

            # 把提取出来的命令发给agent，让它里面设定抽象状态啥的。
            self.redAgent.set_commands(commands) # 得专门给它定制一个发命令的才行，不然不行。            
            pass
        else:
            # 那就正常执行shadow step
            pass

        pass 

    def human_intervene_check(self):
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
        return self.dialog_box.flag_order_renewed, command_str
    
    def main_loop(self):
        # 这个是类似之前的auto_run的东西，跟平台那边要保持交互的。
        timestep = 0 # 每个episode的步数
        log_file = auto_save_file_name(log_folder=r'C:\Users\42418\Desktop\2024ldjs\EnglishMulu\auto_test')
        
        # 训练环境初始化，并返回红蓝方舰船编号
        print("begin resetting")
        shipIDlist = self.env.Reset()
        # shipIDlist = json.loads(shipIDlist)

        redAgent = self.redAgent
        blueAgent = self.blueAgent

        # 红蓝方智能体全局变量初始化
        redAgent.reset()
        blueAgent.reset()
        print("finish resetting")
        s= []
        u = []
        s_next = []

        # 舰船射前部署
        act = []
        # print("shipIDList ", shipIDlist)
        # act += redAgent.deploy(shipIDlist['RedShipID'])
        # act += blueAgent.deploy(shipIDlist['BlueShipID'])
        act += redAgent.deploy()
        act += blueAgent.deploy()
        action = {"Action": act}
        print("action ", action)
        self.env.Step(Action = action)

        # 获取红蓝方态势信息
        cur_redState, cur_blueState = get_states(self.env)
        tips = '\n start main loop: \n'
        # cur_redState_str, start_redState_list = auto_state_filter(cur_redState)
        # cur_blueState_str, start_blueState_list = auto_state_filter(cur_blueState)
        # auto_save(log_file, tips, cur_redState_str, cur_blueState_str)

        # 开搞之前存一下本次测试的配置，xxh0920
        strbuffer = "\n\n现在是" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + "，开始执行测试。\n 测试配置：\n"

        auto_save_overall(strbuffer, log_file=self.log_file)

        # 智能体与环境交互生成训练数据
        while True:
            self.env.SetRender(True) # 训练界面可视化：False --> 关闭
            act = []
            action = {"Action": act}
            # 红蓝方智能体产生动作
            act += redAgent.step(cur_redState) # 原则上这一层应该是不加东西的
            if timestep % 30 == 0:
                self.run_one_step()
            else:
                self.run_one_step_shadow

            act += redAgent.Gostep_abstract_state(cur_redState)
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
                strbuffer = "在第"+str(timestep)+"帧有"+str(blueState_diff_num)+"个目标被摧毁，是" + blueState_diff_str
                auto_save_overall(strbuffer)
            # 红方就先不写了，不然全是导弹子弹被摧毁，乱的一B

            # 记录每一轮运行的日志。面向过程编程还是难受，应该一开始就别偷懒。
            tips = '\n timestep now: ' + str(timestep) + '\n'
            tips = tips + auto_state_compare(cur_blueState_list, start_blueState_list)
            auto_save(log_file, tips, cur_redState_str, cur_blueState_str)
            timestep += 1

            cur_redState = next_redState
            cur_blueState = next_blueState

            # 一个对战回合结束进入下一回合
            if timestep > self.max_episode_len:
                # 获取当前分数
                cur_result = json.loads(self.env.GetCurrentResult())
                blueScore_str = "blueScore: " + str(cur_result["blueScore"])
                redScore_str = "redScore: " + str(cur_result["redScore"])
                print(redScore_str)
                print(blueScore_str)
                tips = '\n get result: timestep =' + str(timestep) + '\n'
                # auto_save(log_file, tips, cur_result)
                auto_save(log_file, tips, redScore_str, blueScore_str)
                # result = env.Terminal()
                auto_save_overall(blueScore_str + '\n' + redScore_str)
                break        
        pass 

if __name__ == "__main__":
    # 这个是总的测试的了
    shishi = command_processor()
    shishi.main_loop()