import os.path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent.base_agent import BaseAgent
import copy
import random


class LocalAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.target_LLA = [100.165, 13.6586,0 ] 
        self.__init_function_dict()
        self.status_unit_memory = dict()
        


    def __init_function_dict(self):
        self.step_function_dict = dict()
        # 此处应当给出通信受限条件下各种情况的处理方式。本例给出一个字典，以实现不同装备类型的单位和其行为函数的对应关系。
        for i in range(len(self.unit_type_list)):
            if i %2 == 0:
                self.step_function_dict[self.unit_type_list[i]] = self.step_0
            else:
                self.step_function_dict[self.unit_type_list[i]] = self.step_1

    def step(self,status_local,unit_id):
        # 这里或许不一定需要unit_id,后面搞着看呗。
        self.act = [] 
        self.status = status_local 
        unit_type = self.get_unit_type(unit_id)
        step_function = self.step_function_dict[unit_type]
        step_function(status_local,unit_id)

        return self.act

    
    # 定义不同装备类型、不同情况下的单位行为。
    def step_0(self,status_local,unit_id):
        d_l = random.uniform(0,1) * 0.001
        self._Move_Action(unit_id,self.target_LLA[0],self.target_LLA[1]+d_l,self.target_LLA[2])
        pass 
    
    def step_1(self,status_local,unit_id):
        d_l = random.uniform(0,1) * 0.001
        self._Move_Action(unit_id,self.target_LLA[0]+d_l,self.target_LLA[1],self.target_LLA[2])
        pass 

    def update_unit_memory(self,status_old):
        # 此处给出一个例子，表示通信受限的装备能够记得它受限之前接收到过的态势信息。
        self.status_unit_memory = copy.deepcopy(status_old)
        pass

    