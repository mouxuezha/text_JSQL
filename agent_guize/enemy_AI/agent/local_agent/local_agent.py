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
        self.flag_standingby = True # 这个标志位用来区分能不能接收命令。主要是如果开了反干扰那个，就不更新命令了。
        self.num_order_start = 0 

    def __init_function_dict(self):
        self.step_function_dict = dict()
        # 此处应当给出通信受限条件下各种情况的处理方式。本例给出一个字典，以实现不同装备类型的单位和其行为函数的对应关系。
        for i in range(len(self.unit_type_list)):
            unit_type_single = self.unit_type_list[i]
            if ("ArmoredTruck" in unit_type_single) or ("ShipboardCombat" in unit_type_single) \
                or ("MainBattleTank" in unit_type_single):
                # 用跑的快的东西去把它冲了
                self.step_function_dict[self.unit_type_list[i]] = self.step_ours_anti_Jammer
            # if i %2 == 0:
            #     self.step_function_dict[self.unit_type_list[i]] = self.step_ours_anti_Jammer
            else:
                self.step_function_dict[self.unit_type_list[i]] = self.step_ours_basic
    
    def receive_order(self,abstract_state_single,**kargs):
        
        if "model" in kargs:
            model = kargs["model"]
        else:
            model = "void"

        if model == "force":
            self.flag_standingby=True

        if self.flag_standingby:
            # 那就是正常接收命令。
            self.abstract_state = abstract_state_single
        else:
            # 那就是进入了不接全局命令的状态了
            pass



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

    def step_ours_basic(self, status_local,unit_id):
        # 原则上什么也不做，继续根据之前的抽象状态来执行。
        # 但是探测还是得探测的，好在探测已经写入Gostep_abstract_state里面了
        self.act = self.Gostep_abstract_state()
        return self.act
    
    def step_ours_anti_Jammer(self,status_local,unit_id):
        # 这个是，如果受到干扰，就直着冲过去给他A了。
        if self.num_order_start == 0:
            # 那就是没有正在阻塞运行的命令。
            self.num_order_start = self.num 
        # 如果detectedstate2里面有干扰车，且进入到了这里，那么就说明是对面干扰开了。
        # 那么相应的装备就应该冲过去给它A了。
        flag_detected = False
        self.flag_standingby = False # 这个就先不收别的指令了
        enemy_id_selected = ""
        for enemy_id in self.detected_state2:
            if "Jamm" in enemy_id:
                flag_detected=True
                enemy_id_selected = enemy_id
        
        if flag_detected and (self.num % 43==5):
            # 那就是找到敌人的了，那就A过去 # 不要每一步都更新，容易卡住出问题
            # 先把敌方的位置拿出来
            target_LLA = self.detected_state2[enemy_id_selected]["this"]["LLA"]
            self.set_move_and_attack(unit_id, target_LLA)
        
        self.act = self.Gostep_abstract_state()
        # 需要设定一个退出机制。比如多少步看不见敌方干扰车的话就算了。
        if (self.num - self.detected_state2[enemy_id_selected]["this"]["num"]>100) or \
           (self.num - self.num_order_start > 500):
            self.flag_standingby = True 
            self.num_order_start = 0 
        return self.act


    def update_unit_memory(self,status_old):
        # 此处给出一个例子，表示通信受限的装备能够记得它受限之前接收到过的态势信息。
        self.status_unit_memory = copy.deepcopy(status_old)
        pass

    