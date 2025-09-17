import os.path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent.base_agent import BaseAgent
import copy

import numpy as np 

class GlobalAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.reset_here()

    def reset_here(self):
        self.test_config =dict()
        self.num = 0
        # 还要清理一些设置。不然连续跑的时候是不对的。
        self.red_step_config = dict() # 这个统一用来存那种“想要开个成员变量记一下”的东西，方便后面写程序。
        self.blue_step_config = dict() # 蓝方的要分开。
        self.act = [] 

    def communication(self, local_agents:dict):
        # 这个用于实现global和没有受到干扰的agent之间的通信。

        # 如果是我们的自己的代码，这里就可以用于传递抽象状态了
        # 那么现在确实是我们自己的代码。

        # 找出能通信的智能体
        for unit_id_single in list(local_agents.keys()):
            # 把它的abstract_state弄出来
            abstract_state_single = {unit_id_single: self.abstract_state[unit_id_single]}
            local_agent_single = local_agents[unit_id_single]
            # 给到local的里面。按理来说，都是传引用的话，到这里就算是完事儿了。调试的时候注意看一眼。
            # local_agent_single.abstract_state = abstract_state_single
            local_agent_single.receive_order(abstract_state_single)

            # 然后把当前能看到的态势也都发进去。
            local_agent_single.detected_state2 = self.detected_state2
            local_agent_single.detected_state = self.detected_state
            
            # 然后是当前的命令设定，也得更新进去。
            # local_agent_single.group_A_gai_config = self.group_A_gai_config
        
        
        pass

    def step(self,status:dict):
        self.act = [] 
        self.status = status
        # print("unfinished yet")
        if self.player == "red":
            # 当前智能体是红方
            # self.act = self.step_red_shishi1(status)
            # self.act = self.step_red_shishi2(status)
            # self.act = self.step_red_xunfeidan(status)
            # self.act = self.step_red_shangxiache(status)
            self.act = self.step_red_2025_test(status)
            # self.act = self.step_LLM(status)
            pass
        elif self.player == "blue":
            # 当前智能体是蓝方
            # self.act = self.step_blue_shishi1(status)
            # self.act = self.step_blue_shishi2(status)
            # self.act = self.step_blue_shishi3(status)
            # self.act = self.step_blue_shangxiache(status)
            # self.act = self.step_LLM(status)
            self.act = self.step_blue_2025_test(status)
            pass 
        return self.act
    
    def reset(self):
        super().reset()
        self.reset_here()
        # print("unfinished yet")
        pass



    def load_test_config(self,test_config):
        self.test_config = self.test_config | test_config
        pass

    
    def step_red_2025_test(self,status:dict):
        
        truck_units = self.select_by_type("Truck_Ground")
        UAV_unit = self.select_by_type("Recon_UAV_FixWing")
        kuaiting_unit = self.select_by_type("Guide_Ship_Surface")

        if self.num == 10:
            target_LLA = [46.9897,12.0050,0]
            self.set_mission_focus_fire(truck_units, "", target_LLA=target_LLA,weapon_type="HighCostAttackMissile") # 这个有一个问题就是依赖于探测。没探测了就歇了。
            # self.set_mission_focus_fire(truck_units, "", target_LLA=target_LLA,weapon_type="LowCostAttackMissile") # 这个有一个问题就是依赖于探测。没探测了就歇了。
            
            self.set_mission_scout((UAV_unit | kuaiting_unit),space_arrange=[46.0,12.0,48.0,11.0]) # 好，几乎完事了. 
            # self.set_mission_supresse_fire(truck_units,space_arrange=[46.0,12.0,48.0,11.0],)
        
        # 这句统一拿出来外面写了。
        self.act = self.Gostep_all()
        return self.act 

    def step_blue_2025_test(self,status:dict):
        CG_units = self.select_by_type("Cruiser_Surface")
        DD_unit = self.select_by_type("Destroyer_Surface")
        CVN_unit = self.select_by_type("Flagship_Surface")
        plan_unit = self.select_by_type("Shipboard_Aircraft_FixWing")
        ship_unit = CG_units | DD_unit 

        if self.num == 11:
            # 蓝方主要是得把拦截的测了，不然玩不了。态势过滤的时候打鸡蛋得在里面
            target_LLA = [46.340332,11.296934,0]
            self.set_mission_scout(plan_unit,space_arrange=[43.6508, 14.80, 49.6314, 12.5836]) # 几乎完事了，尚欠火力打击。
            self.set_mission_preserve(ship_unit,enemy_direction = [0,1,0])

        # 这句统一拿出来外面写了。
        self.act = self.Gostep_all()
        return self.act 

    def step_LLM(self,status:dict):
        # 用于配合大模型的。说白了就是啥也不干，只维护抽象状态和任务进展。

        self.act = self.Gostep_all()
        return self.act     