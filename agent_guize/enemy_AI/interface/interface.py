# 这个是用于配合推演模式调用的时候用的。以尽量少改为原则。

import os.path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import auto_run
from agent.agent_dispatch import agent_dispatch
import json
from support.tools import *
import threading 


class interface(auto_run):
    # 直接给它冲了，直接类继承就完事儿了。虽然容易变成屎山，但是好在这里能弄的不多。
    def __init__(self,player="red"):
        super().__init__()
        self.selected_palyer = player
        # 按说应该不初始red和blue，以防变成屎山。但是都初试好了再来del嘛又显得过于刻意。
        # del self.redAgent
        # del self.blueAgent

        self.init_agents(player=player)
        pass

    def init_agents(self,player="red"):
        # 先初始化智能体，只初始化一个就是了
        self.redorblue_Agent = agent_dispatch(player=player)
        self.selected_palyer = player

    def run_redorblue(self):
        # 这个就是原汁原味，纯而又纯，不带参数的自动跑。
        redorblue_Agent = self.redorblue_Agent

        for ep in range(self.net_args.epochs):
            print("================ {} th =============".format(ep + 1))
            self.run_single_redorblue(redorblue_Agent)        

    def run_single_redorblue(self, redorblue_Agent:agent_dispatch):
        args = self.net_args
        env = self.env
        timestep = 0 # 每个episode的步数
        print("begin resetting")
        unit_ids_dict = env.Reset()
        unit_ids_dict = json.loads(unit_ids_dict) 

        # 和去年的不同，这里要初始化global和local
        if self.selected_palyer == "red":
            ID_tag = 'RedShipID'
        elif self.selected_palyer == "blue":
            ID_tag = "BlueShipID"
        else:
            raise Exception("run_single_redorblue: invalid ID_tag")
        
        redorblue_Agent.init_agent(unit_ids_dict[ID_tag])   


        # 红蓝方智能体全局变量初始化
        redorblue_Agent.reset()
        print("finish resetting")

        if self.selected_palyer == "red":
            env.SetRedRecvScene()
        elif self.selected_palyer == "blue":
            env.SetBlueRecvScene()

        # 开局前进行一番部署
        act = []
        print("unit_ids_dict ", unit_ids_dict)
        

        act += redorblue_Agent.deploy(unit_ids_dict[ID_tag])
        action = {"Action": act}
        print("action ", action)
        env.Step(Action = action)
        

        # 获取红蓝方态势信息
        cur_redState, cur_blueState = get_states(env)

        while True:
            env.SetRender(True) # 训练界面可视化：False --> 关闭
            act = []

            if self.selected_palyer == "red":
                cur_State = cur_redState
                timestep = cur_State["redbmc3"]["simTime"]
            else:
                cur_State = cur_blueState
                timestep = cur_State["bluebmc3"]["simTime"]

            # 这个是服务于咱自己的AI的
            try:
                if len(redorblue_Agent.global_agent.abstract_state)==0:
                    redorblue_Agent.global_agent.Inint_abstract_state(cur_State)
            except:
                pass
                
            # 红蓝方智能体产生动作

            # 加个容错，防止参赛队的程序跑崩了。
            try:
                act += redorblue_Agent.step(cur_State)
            except:
                print("interface: running wrong in " + self.selected_palyer)

            action = {"Action": act}

            env.Step(Action = action)
            next_redState, next_blueState = get_states(env)

            cur_result = json.loads(env.GetCurrentResult())
            
            
            #timestep += 1
            print("timestep:",timestep)

            cur_redState = next_redState
            cur_blueState = next_blueState

            # 一个对战回合结束进入下一回合
            if (timestep % 10 == 0) or (timestep > args.max_episode_len):
                print("running, timestep = "+str(timestep))
                # 获取当前分数
                cur_result = json.loads(env.GetCurrentResult())
                blueScore_str = "blueScore: " + str(cur_result["blueScore"])
                redScore_str = "redScore: " + str(cur_result["redScore"])
                print(redScore_str)
                print(blueScore_str)
                # tips = '\n get result: timestep =' + str(timestep) + '\n'
                # result = env.Terminal()
                if (timestep > args.max_episode_len):

                    break        
        return 0

def test_red_and_blue():
    # 这个是用来debug的，就是开两个线程，把测试做了。
    runner_red = interface("red")
    runner_blue = interface("blue")

    thread1 = threading.Thread(target=runner_red.run_redorblue)
    thread2 = threading.Thread(target=runner_blue.run_redorblue)     

    thread1.start()
    thread2.start()

if __name__ == "__main__":
    # 经过简简单单的一番修改，看起来就能行了。
    # print("别直接运行这个，要运行去运行带了red和blue的那个。")
    test_red_and_blue()
    # 命令行开的命令如下，想要red或者blue自己换就是了。
    # D:\software\Anaconda\conda\envs\shishi_MQ\python.exe D:\EnglishMulu\AI_test_2024\interface\interface.py