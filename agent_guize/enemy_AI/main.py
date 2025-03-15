# 这个里面封装了一些调用的逻辑，区分了test啥的。
from support.Env import Env,Env_demo
from agent.agent_dispatch import agent_dispatch
from support.tools import *

import json
import time 
import argparse
import sys,os,pickle
from importlib import import_module
import threading 

class auto_run(object):
    def __init__(self) -> None:
        self.__init_net()

        self.__init_env()
        
        self.timestep=0

        self.init_agents()
        self.save_location = r"auto_test"
        pass

    def __init_env(self):
        self.max_episode_len = self.net_args.max_episode_len
        self.env = Env(self.net_args.ip, self.net_args.port)

    def __init_net(self):
        parser = argparse.ArgumentParser(description='Provide arguments for agent.')
        parser.add_argument("--ip", type=str, default="127.0.0.1", help="Ip to connect")
        # parser.add_argument("--ip", type=str, default="192.168.43.93", help="Ip to connect")
        parser.add_argument("--port", type=str, default=20001, help="port to connect")
        parser.add_argument("--epochs", type=int, default=200, help="Number of training epochs to run")  # 设置训练轮次数
        parser.add_argument("--max-episode-len", type=int, default=5000, help="maximum episode length")
        net_args = parser.parse_args()
        self.net_args = net_args
        return net_args    
    
    def __init_exe(self):
        # 这个是纯辅助的，把它关了手动点一遍也是可以的

        cmd_order1 = r"F: & cd F:\ruanjian_M\DemoBin & 中间件.exe"
        cmd_order2 = r"F: & cd F:\ruanjian_M\JSQL_Display3D & 白方显示.exe"
        # os.system(cmd_order1) # 还是这个靠谱，subprocess.Popen会报权限问题
        cmd_order_list = [cmd_order1,cmd_order2] 
        geshu = len(cmd_order_list)
        self.exe_thread_list = [] 

        for i in range(geshu):
            # 先初始化一堆线程，然后在里面给它润起来，然后再说别的。
            thread_single = threading.Thread(target=self.__init_exe_single,args=(cmd_order_list[i],))
            self.exe_thread_list.append(thread_single)
        # 然后全部启动一遍然后就摆了
        for i in range(geshu):
            thread_single = self.exe_thread_list[i]
            thread_single.start()
            time.sleep(5)    

        print("这会儿应该把前端起起来了。")    

    def __init_exe_single(self,cmd):
        cmd_order1 = cmd
        os.system(cmd_order1) # 还是这个靠谱，subprocess.Popen会报权限问题                
    
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
    
    def init_agents(self):
        # 先初始化出来双方的智能体.
        self.redAgent = agent_dispatch(player="red")
        self.blueAgent = agent_dispatch(player="blue")
    
    def run_single(self,redAgent:agent_dispatch,blueAgent:agent_dispatch):
        # 完成一把对局，不采集test数据。不采集、不自动的话就简单多了。别慌，先把原始的干净版本弄出来，再搞自动对局需要的版本。
        # 回头把craftgame manager那套挪过来可也。
        # 相当于这里面只跑一个episode，然后尽量简化

        args = self.net_args
        env = self.env
        timestep = 0 # 每个episode的步数
        print("begin resetting")
        unit_ids_dict = env.Reset()
        unit_ids_dict = json.loads(unit_ids_dict) 

        # 和去年的不同，这里要初始化global和local
        redAgent.init_agent(unit_ids_dict['RedShipID'])
        blueAgent.init_agent(unit_ids_dict['BlueShipID'])     


        # 红蓝方智能体全局变量初始化
        redAgent.reset()
        blueAgent.reset()
        print("finish resetting")

        # 开局前进行一番部署
        act = []
        print("unit_ids_dict ", unit_ids_dict)
        act += redAgent.deploy(unit_ids_dict['RedShipID'])
        act += blueAgent.deploy(unit_ids_dict['BlueShipID'])
        action = {"Action": act}
        print("action ", action)
        env.Step(Action = action)
        

        # 获取红蓝方态势信息
        cur_redState, cur_blueState = get_states(env)

        while True:
            env.SetRender(True) # 训练界面可视化：False --> 关闭
            act = []
                
            # 红蓝方智能体产生动作
            act += redAgent.step(cur_redState)
            act += blueAgent.step(cur_blueState)

            action = {"Action": act}

            env.Step(Action = action)
            next_redState, next_blueState = get_states(env)

            cur_result = json.loads(env.GetCurrentResult())
            
            timestep += 1


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

    def run(self):
        # 这个就是原汁原味，纯而又纯，不带参数的自动跑。
        redAgent = self.redAgent
        blueAgent = self.blueAgent

        for ep in range(self.net_args.epochs):
            print("================ {} th =============".format(ep + 1))
            self.run_single(redAgent, blueAgent)

    def run_test(self,**kargs):
        # 完成一把对局，加载测试部署，采集各种各样的数据，还得存下来。
        # def train(redAgent: RedAgent, blueAgent: BlueAgent, args, seed=1234,**kargs):
        redAgent = self.redAgent
        blueAgent = self.blueAgent
        args = self.net_args
        env = self.env
        log_file = auto_save_file_name(log_folder=r'auto_test') # 能改相对路径尽量改成相对路径。
        for ep in range(args.epochs):
            print("================ {} th =============".format(ep + 1))
            timestep = 0 # 每个episode的步数
            # 训练环境初始化，并返回红蓝方舰船编号
            print("begin resetting")
            unit_ids_dict = env.Reset()
            unit_ids_dict = json.loads(unit_ids_dict)

            # 和之前的不同，这里要初始化global和local
            redAgent.init_agent(unit_ids_dict['RedShipID'])
            blueAgent.init_agent(unit_ids_dict['BlueShipID'])

            # 红蓝方智能体全局变量初始化
            redAgent.reset()
            blueAgent.reset()
            print("finish resetting")

            # 开局前进行一番部署
            act = []
            print("unit_ids_dict ", unit_ids_dict)
            act += redAgent.deploy_test(unit_ids_dict['RedShipID'])
            act += blueAgent.deploy_test(unit_ids_dict['BlueShipID'])
            action = {"Action": act}
            print("action ", action)
            env.Step(Action = action)

            # 获取红蓝方态势信息
            cur_redState, cur_blueState = get_states(env)
            tips = '\n start one ep: ' + str(ep) + '\n'
            cur_redState_str, start_redState_list = auto_state_filter(cur_redState)
            cur_blueState_str, start_blueState_list = auto_state_filter(cur_blueState)
            auto_save(log_file, tips, cur_redState_str, cur_blueState_str)
            # print(cur_redState)
            #
            # # 获取地形
            # print('landform:')
            # print(env.GetLandForm(2.6801, 39.701))

            # 开搞之前存一下本次测试的配置，xxh0920
            if "target_location" in kargs:
                target_location = kargs['target_location']
            else:
                target_location = self.save_location 

            strbuffer = "\n\n现在是"+log_file+"\n本轮配置：" + "  " + kargs['my_unit_type'] + "  " + kargs['my_weapon_type'] + "  " + \
                        kargs['target_unit_type'] + "  " + str(target_location) + "  " + kargs['target_state']
            
            # 这个是测量取地形的，带着随便测一下好了，这环节出问题的概率不是很高。
            dixing_dic = env.GetLandForm(target_location[0], target_location[1])
            try:
                dixing_dic = eval(dixing_dic)
                dixing_str = dixing_dic["landform"]
                strbuffer = strbuffer + "\n 设定地形和实际地形：" + kargs['target_landform'] + "  " + dixing_str
            except:
                print("XXHtest: fail to get landform, G")
            auto_save_overall(strbuffer,log_file=self.save_location + r'\kaihuo\overall_result.txt')

            # 智能体与环境交互生成训练数据
            while True:
                env.SetRender(True) # 训练界面可视化：False --> 关闭
                act = []
                
                # 红蓝方智能体产生动作
                act += redAgent.step(cur_redState)
                act += blueAgent.step(cur_blueState)

                action = {"Action": act}

                env.Step(Action = action)
                next_redState, next_blueState = get_states(env)

                # 这里来一段，识别一下这一帧是否有装备毁伤。
                cur_redState_str, cur_redState_list = auto_state_filter(cur_redState)
                cur_blueState_str, cur_blueState_list = auto_state_filter(cur_blueState)
                next_redState_str, next_redState_list = auto_state_filter(next_redState)
                next_blueState_str, next_blueState_list = auto_state_filter(next_blueState)

                cur_result = json.loads(env.GetCurrentResult())
                redState_diff_str, redState_diff_num = auto_state_compare2(cur_redState_list, next_redState_list)
                blueState_diff_str, blueState_diff_num = auto_state_compare2(cur_blueState_list, next_blueState_list)
                if blueState_diff_num>0:
                    # 说明在这一帧有蓝方装备被摧毁，值得写一条日志。
                    strbuffer = "在第"+str(timestep)+"帧有"+str(blueState_diff_num)+"个目标被摧毁，是" + blueState_diff_str
                    auto_save_overall(strbuffer,log_file=self.save_location + r'\kaihuo\overall_result.txt')
                # 红方就先不写了，不然全是导弹子弹被摧毁，乱的一B

                # 记录每一轮运行的日志。面向过程编程还是难受，应该一开始就别偷懒。
                tips = '\n timestep now: ' + str(timestep) + '\n'
                tips = tips + auto_state_compare(cur_blueState_list, start_blueState_list)
                auto_save(log_file, tips, cur_redState_str, cur_blueState_str)
                timestep += 1

                cur_redState = next_redState
                cur_blueState = next_blueState

                # 一个对战回合结束进入下一回合
                if timestep > args.max_episode_len:
                    # 获取当前分数
                    cur_result = json.loads(env.GetCurrentResult())
                    blueScore_str = "blueScore: " + str(cur_result["blueScore"])
                    redScore_str = "redScore: " + str(cur_result["redScore"])
                    print(redScore_str)
                    print(blueScore_str)
                    tips = '\n get result: timestep =' + str(timestep) + '\n'
                    # auto_save(log_file, tips, cur_result)
                    auto_save(log_file, tips, redScore_str, blueScore_str)
                    # result = env.Terminal()
                    auto_save_overall(blueScore_str + '\n' + redScore_str,log_file=self.save_location + r'\kaihuo\overall_result.txt')
                    break

            # 红蓝方智能体获取全局态势，计算奖励值
            # info = env.reward()
            # r = redAgent.compute_reward(result, info)
            # blueAgent.compute_reward(info)

            # --------------------replay buffer内存储训练样本--------------------
            # for i in range(len(u)):
            #     redAgent.buffer.store_episode(s[i], u[i], r, s_next[i])
            # --------------------replay buffer内存储训练样本--------------------

            # for _ in range(40):
            #     redAgent.learn()
    
    def run_auto_test_kaihuo(self):
        #这个是把去年的自动测试的恢复起来。今年做好版本管理，确保可用性。
        # xxh 0908, 尝试进行自动化测试。# 2024年8月6日，进行现代化改装。

        # 先搞点装备list进来。# 能用相对目录就还是尽量用相对目录了，给他弄得专业一点。
        # file_name = 'C:/Users/yfzx/Desktop/2024ldjs/EnglishMulu/AI_test_2024/auto_test/kaihuo/kaihuo_test_config.xlsx'
        file_name =self.save_location + r"\kaihuo\kaihuo_test_config.xls"

        try:
            kaihuo_test_config_workbook = xlrd.open_workbook(file_name)
        except FileNotFoundError:
            print('注意，没读取到文件，AgentTrain里面有硬编码地址')
            return -1

        kaihuo_test_config_sheets = kaihuo_test_config_workbook.sheets()
        kaihuo_test_config = kaihuo_test_config_sheets[0]._cell_values
        geshu = len(kaihuo_test_config)

        # 再安排上目标点地域
        # file_name = r'E:\XXH\auto_test\kaihuo_test_config2.xlsx'
        file_name =self.save_location + r"\kaihuo\kaihuo_test_config2.xls"
        try:
            kaihuo_test_config2_workbook = xlrd.open_workbook(file_name)
        except FileNotFoundError:
            print('注意，没读取到文件，AgentTrain里面有硬编码地址')
            return -1
        kaihuo_test_config2_sheets = kaihuo_test_config2_workbook.sheets()
        kaihuo_test_config2 = kaihuo_test_config2_sheets[0]._cell_values
        geshu2 = len(kaihuo_test_config2)

        # 设定一下部署的地方
        self.redAgent.set_deploy_folder(self.save_location + r"\kaihuo\reddeploy")
        self.blueAgent.set_deploy_folder(self.save_location + r"\kaihuo\bluedeploy")

        # 更改AI设定，把相应的装备弄到相应的位置去。
        # 修改步数:
        # args.epochs = 24
        self.net_args.epochs = 1 # 只走一次，因为要重新初始化
        self.net_args.max_episode_len = 300 # 看情况，具体需要走多少帧。
        attacker_state = 'stay' # 这个还是先分开，不要想着一口气全安排上，不要飘。

        # 获取现有进度。
        existing_index = auto_save_check_index(log_folder=self.save_location + r"\kaihuo")
        existing_index = existing_index % geshu # 看一下第一张表遍历到哪里了。

        existing_index2 = auto_save_check_index(log_folder=self.save_location + r"\kaihuo")
        existing_index2 = existing_index2 // geshu2  # 看一下第二张表遍历到哪里了。

        # 初始化agent里面，用于传参数。
        print("begin resetting")
        unit_ids_dict = self.env.Reset()
        unit_ids_dict = json.loads(unit_ids_dict)

        # 和之前的不同，这里要初始化global和local
        self.redAgent.init_agent(unit_ids_dict['RedShipID'])
        self.blueAgent.init_agent(unit_ids_dict['BlueShipID'])

        for i in range(geshu-existing_index):
            for j in range(geshu2 - existing_index2):

                # 正常来说是自动续算。
                jindu1 = i + existing_index
                jindu2 = j + existing_index2

                # 排故的时候是指定特定的参数组合。
                # jindu1 = 12
                # jindu2 = 0

                my_unit_type = kaihuo_test_config[jindu1][0]
                my_weapon_type = kaihuo_test_config[jindu1][1]
                target_unit_type = kaihuo_test_config[jindu1][2]

                target_landform = kaihuo_test_config2[jindu2][0]
                target_location = [kaihuo_test_config2[jindu2][1], kaihuo_test_config2[jindu2][2], 0]
                target_state = kaihuo_test_config2[jindu2][3]

                redAgent = self.redAgent
                blueAgent =  self.blueAgent

                # redAgent.deploy_modify_set(my_unit_type, my_weapon_type, target_unit_type, location=[2.68, 39.70, 0], index=0)
                # blueAgent.deploy_modify_set(target_unit_type, my_weapon_type, my_unit_type, location=[2.6801, 39.701, 0], index=0)

                redAgent.deploy_modify_set(my_unit_type, my_weapon_type, target_unit_type,location=[target_location[0]-0.008, target_location[1]-0.0008, 0], index=0, target_location = target_location )

                # redAgent.deploy_modify_set(my_unit_type, my_weapon_type, target_unit_type,location=[100.12726665,13.64277031, 0], index=0, target_location = target_location )
                             
                blueAgent.deploy_modify_set(target_unit_type, my_weapon_type, my_unit_type, location=target_location, index=0)

                redAgent.deploy_modify_getstate(attacker_state)
                blueAgent.deploy_modify_getstate(target_state)

                # if(my_weapon_type == 'ArmorPiercingShot_ZT'):
                if (True):
                    self.run_test(my_unit_type=my_unit_type, my_weapon_type=my_weapon_type, target_unit_type=target_unit_type,
                    target_landform=target_landform, target_location=target_location, target_state=target_state)

        # 一定步数后完成运行，开个log记录相应的输出。
            
if __name__ == "__main__":

    runner = auto_run()
    # runner.run_auto_test_kaihuo()
    runner.run()
