# 这里提供一个简化版的从子任务序列映射到行动序列的东西。
import os.path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import dill 

from agent_guize.enemy_AI.agent.base_agent import BaseAgent
import random,copy 

class plan_interface(BaseAgent):
    def __init__(self):
        super().__init__()

        model2_location = r"D:/EnglishMulu/test_decision"
        if not(os.path.exists(model2_location)):
            raise Exception("plan_interface：没能正确找到模块2相关代码")
        else:
            sys.path.insert(0, model2_location)
        self.index = 0
        self.plan_list = [] # 这个还是得存的嘛。
        self.plan_location_list = [] 
        self.action_list = [] # 里面的元素应该是个dict，num:int, commands:list # 跟这个一个数据结构应该。commands = self.text_transfer.text_to_commands(response_str)
        # 讲道理，action不是提前生成的，得是根据态势啥的现场计算一个才行。但是在最拉的初始版本里面，先尽量简化
        # 这得琢磨一下咋弄。

        self.num = 0 
        self.unit_type = ["坦克和自行迫榴炮", "装甲车等其他地面力量", "无人机和巡飞弹"]
        pass

    def load_plans(self,plan_location_list:list):
        # 这个就是读入方案了，plan_location_list里面是各个方案的路径。
        self.plan_location_list = plan_location_list
        for i in range(len(self.plan_location_list)):
            plan_single = self.load_plan(self.plan_location_list[i])
            self.plan_list.append(plan_single)
            # try:
            #     plan_single = self.load_plan(self.plan_location_list[i])
            #     self.plan_list.append(plan_single)
            # except:
            #     print("plan {} load failed".format(i))
        
        print("plan_interface: finish load plans.")

    def load_plan(self,plan_location:str):
        # 这个就是读入单个方案了。
        with open(plan_location, 'rb') as f:
            plan = dill.load(f)
        # self.plan_list.append(plan)
        return plan
    
    def set_plan(self, index:int):
        # 这个就是选择第几个计划的意思。
        self.index = index
        print("选定的计划为第"+str(self.index)+"个")

    def get_action_one_step(self, num:int, status:dict):
        # 这个应该是每一步都调用一次，然后根据态势和步数判断是不是需要增加或者修改新commands。
        self.num = num # 不要自增，而是从外面同步进来。

        # 先遍历每一个子任务，选出开始于当前步数的，然后根据子任务和status来生成action
        submissions_this_step = self.check_submission()

        # 需要搞一个默认值，如果已经很多帧没有动静了，就向北进攻一段，或者说向中间进攻一段。
        submissions_this_step=self.get_defualt_submission()

        # 然后开始生成了。
        commands_all = []
        for submission in submissions_this_step:
            # 每一个子任务生成一组commands，然后联系起来
            commands_single = self.generate_actions(submission,status)
            commands_all = commands_all + commands_single
            pass

        # 然后把这玩意记录到数据结构里面。
        # action_list_single = {"num":self.num, "commands":commands_all}
        # self.action_list.append(action_list_single)

        # 搞专业点，这里做个异步的机制。这些命令在随后的一定步数中随机出。
        # 先加上随机数存到list里面。
        for command_single in commands_all:
            num_randm = self.num + random.randint(0,50)
            action_single = {"num":num_randm, "commands":command_single}
            self.action_list.append(action_single)
        
        # 然后再从list里面找当前的。注意保持数据结构的一致性。
        commands_this_step = self.check_action_list(self.num)

        return commands_this_step

    def check_submission(self):
        selected_plan = self.plan_list[self.index]
        selected_submissions = selected_plan.submission_list
        submissions_this_step = [] 
        for i in range(len(selected_submissions)):
            # 检查每一个子任务。
            if selected_submissions[i].time_arrange[0] == self.num:
                submissions_this_step.append(selected_submissions[i])
        return submissions_this_step
    
    def check_last_submission(self, force_arrange:str):
        # 找出分给特定兵力的上一个子任务，看看隔了多久。
        selected_plan = self.plan_list[self.index]
        selected_submissions = selected_plan.submission_list
        last_submission = None
        flag_done = False # 这个标志位用来推测，上一个子任务是不是已经完成了。
        for i in range(len(selected_submissions)):
            # 检查每一个子任务，看是不是分给当前兵力的。
            if selected_submissions[i].force_arrange == force_arrange:
                # 那就看看这个子任务是不是上一个子任务。
                if selected_submissions[i].time_arrange[0] < self.num:
                    # 这样替换完了之后应该能找到“不超过当前时间的最后一个子任务”，那就是上一个子任务。
                    last_submission = selected_submissions[i]
                    # 这里就是强行认为500帧就够执行完之前的子任务了。
                    if selected_submissions[i].time_arrange[0] < self.num - 500: 
                        flag_done = True
                else:
                    # 那就是不是上一个子任务。
                    pass

        # submission_list = selected_plan.submission_list # 这个是返回去给后面用于算默认值用的。
        submission_list = [] 
        # 原则上应该返回一个“刚好到前面一个”的list，算力还是别偷懒，好好弄一下可也。
        for i in range(len(selected_submissions)):
            if selected_submissions[i].time_arrange[0] < self.num:
                submission_list.append(selected_submissions[i])

        # TODO:啊其实最理想的是把它们的位置都取出来，然后逐帧记录，来判断是不是已经没有动静了。
        print("check_last_submission: unfinishd yet")

        return last_submission, flag_done, submission_list
    
    def get_defualt_submission(self):
        # 这个是如果很长时间没有动静了，就生成一个默认的子任务。
        print("unfinishd yet")
        submission_list = [] 
        for unit_type_single in self.unit_type:
            last_submission, flag_done,submission_list = self.check_last_submission(force_arrange=unit_type_single)
            if flag_done:
                # 那就是还没有完成，那就不用管了。
                pass
            else:
                # 那就是已经完成了，那就需要搞一点默认的进来了
                selected_plan = self.plan_list[self.index]
                defualt_submission = selected_plan.decide_default_submission(unit_type_single,self.num,submission_list)
                submission_list.append(defualt_submission)
        return submission_list

    def check_action_list(self,num:int):
        # 从现有的action list里面检索出符合当前步数的，然后输出成一个commands_all。
        # 现在姑且先不管检索效率的事情，现在就突出一个能用就行。
        commands_all = [] 
        for action_single in self.action_list:
            if num == action_single["num"]:
                # 那就是这步应该执行的东西。那就拿出去
                commands_all.append(action_single["commands"])
            else:
                # 那就不是这步的东西。
                pass
        return commands_all

    def generate_actions(self,submission,status):
        # 先把涉及的装备整出来
        unit_selected = self.type_filter(submission.force_arrange,status)
        
        LLA_ave = self.get_LLA_ave(status=unit_selected)
        
        commands = []
        index_local = 0 
        for unit_id in unit_selected:
            index_local = index_local + 1 
            obj_id = unit_id
            LLA_target = copy.deepcopy(LLA_ave)

            # 然后定制一系列的目标点。原则上这一步应该是之前就做好的，但是这里做一下也罢。
            direction = submission.config_json["出击方向"]
            if direction == "偏东":
                # 那就根据平均值往东边去一些。一样的，搞点随机数显得比较阳间
                LLA_target[0] = LLA_target[0] + 0.02 + random.randint(0,10) * 0.0005
                LLA_target[1] = LLA_target[1] + 0.01 + random.randint(0,10) * 0.0001
                pass
            elif direction == "偏西":
                # 那就根据平均值往西边去一些。
                LLA_target[0] = LLA_target[0] - 0.02 - random.randint(0,10) * 0.0005
                LLA_target[1] = LLA_target[1] + 0.01 + random.randint(0,10) * 0.0001            
                pass
            elif direction == "中间":
                # 那就根据平均值往中间多去一些。
                LLA_target[0] = LLA_target[0] - 0.00005 + random.randint(0,10) * 0.0001  
                LLA_target[1] = LLA_target[1] + 0.01 + random.randint(0,10) * 0.0001     
                pass

            if submission.type_str == "陆地进攻":
                command_single = {"type": "move", "obj_id": obj_id, "x": LLA_target[0], "y": LLA_target[1]}
            elif submission.type_str == "空中侦察":
                # 加一些check
                LLA_target[1] = LLA_target[1] + 0.005
                if LLA_target[1]>13.65:
                    LLA_target[1] = 13.65
                command_single = {"type": "move", "obj_id": obj_id, "x": LLA_target[0] + 0.06*(-2+index_local), "y": LLA_target[1]}
            else:
                raise Exception("invalid submission type in generate_actions, G. ")

            commands.append(command_single)
        return commands
            
    
    def type_filter(self,force_arrange,status):
        self.status = status
        bin_status = self.select_by_type("Infantry")
        tank_status = self.select_by_type("MainBattleTank")
        xiaoche_status = self.select_by_type("ArmoredTruck")
        che_status = self.select_by_type("WheeledCmobatTruck")
        feiji_status = self.select_by_type("ShipboardCombat_plane")
        xunfeidan_status = self.select_by_type("CruiseMissile")
        daodan_status = self.select_by_type("missile_truck")
        pao_status = self.select_by_type("Howitzer")
        ganraoche_status = self.select_by_type("JammingTruck")

        if force_arrange == "坦克和自行迫榴炮":
            # unit_selected = tank_status | pao_status | daodan_status
            unit_selected = tank_status | pao_status # 导弹发射车先不要纳入里面，不然算平均值算的就有问题了。
        elif force_arrange == "装甲车等其他地面力量":
            unit_selected = xiaoche_status | che_status | ganraoche_status | bin_status
        elif force_arrange == "无人机和巡飞弹":
            unit_selected = xunfeidan_status | feiji_status
        else:
            raise Exception("invalid force_arrange type in submission, G. ")

        return unit_selected
    
if __name__ == "__main__":
    shishi_interface = plan_interface()
    plan_location_list = [] 
    plan_location_list.append(r"E:/EnglishMulu/text_decision/auto_test/temp/jieguo0.pkl")
    plan_location_list.append(r"E:/EnglishMulu/text_decision/auto_test/temp/jieguo1.pkl")
    plan_location_list.append(r"E:/EnglishMulu/text_decision/auto_test/temp/jieguo2.pkl")
    shishi_interface.load_plans(plan_location_list)
