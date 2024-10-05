
import os.path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import xlrd

from agent.global_agent.global_agent import GlobalAgent
from agent.local_agent.local_agent import LocalAgent
import copy 
import random
import numpy as np 
import queue

class agent_dispatch(object):  # 这个是用来处理分级态势的，注意保持好和之间的接口。也是step然后过滤啥的。
    def __init__(self, player="red") -> None:
        self.status_old = dict() # 这个用于实现记忆功能，默认被干扰了的东西能够共享到被干扰之前的状态。给进去之后自己要不要记录那就是自己的事情了捏。
        

        self.local_agent_num = 16
        # self.local_agent = LocalAgent()
        self.local_agent_dict = dict()

        self.act = [] 
        self.num = 0 # 这个记录推演的步数

        self.player = player # 默认红方，这个参数将会传给其调度的global和local智能体。
        self.deploy_folder = "auto_test"
        self.deploy_modify_flag = False

        # self.init_agent()
        self.unit_ID_list = [] 
        self.status = dict()
        if self.player == "red":
            self.name_list = ["MainBattleTank_ZTZ100", "ArmoredTruck_ZTL100", "WheeledCmobatTruck_ZB100", "Howitzer_C100",
                            "missile_truck", "Infantry", "ShipboardCombat_plane","CruiseMissile", "JammingTruck"] 
        elif self.player == "blue":
            # print("unfinished yet, pause")
            # input()
            self.name_list = ["MainBattleTank_ZTZ200", "ArmoredTruck_ZTL200", "WheeledCmobatTruck_ZB200", "Howitzer_C200",
                            "missile_truck", "Infantry", "ShipboardCombat_plane","CruiseMissile","JammingTruck"]             
        pass
        
        self.commands_queue = queue.Queue(maxsize=114514) # 这个是新加的，用来处理和大模型的交互。

    def init_agent(self, unit_ID_list):
        # 每个装备应该是对应一个局部的智能体的，不然态势同步的时候就乱完了。
        # 这个还不应该是列表，这个还应该是ID的list才比较好。
        if len(list(self.local_agent_dict.keys()))>0:
            # 已经初始化过了，就不再初始化了。
            print("注意,重复初始化agent是不推荐的")
            return
        
        unit_ID_list_filtered = self.unit_id_filter(unit_ID_list)
        local_agent_num = len(unit_ID_list_filtered)
        self.unit_ID_list = unit_ID_list
        for i in range(local_agent_num):
            self.local_agent_dict[unit_ID_list_filtered[i]] = LocalAgent()
            self.local_agent_dict[unit_ID_list_filtered[i]].player = self.player
        
        self.global_agent = GlobalAgent()
        self.global_agent.player = self.player
        print("init_agent: finished")
    
    def reset(self):
        self.global_agent.reset()
        for unit_id_single in self.local_agent_dict:
            self.local_agent_dict[unit_id_single].reset()
        self.act = [] 
        self.status_old = dict()
            

    def step(self,status:dict):
        self.status = status
        self.act = []  # 每一步先把上一步的清了，鉴定为好。
        if self.player=="red":
            self.num = status["redbmc3"]["simTime"]
        elif self.player=="blue":
            self.num = status["bluebmc3"]["simTime"]

        # 这得有个说法，过滤出两个list，分别给到两个类型的agent里面去。
        status_global, status_local_list, unit_ids_global, unit_ids_local = self.status_filter(status)

        # 然后各自调用各自的好了
        # 先是调用local的。
        for i in range(len(unit_ids_local)):
            unit_id_single = unit_ids_local[i]
            status_single = status_local_list[i]
            flag_update = self.check_update_local(unit_id_single, self.status_old)
            self.local_agent_dict[unit_id_single].num = self.num # 当前推演进程应该同步到各个装备上。
            if flag_update:
                self.local_agent_dict[unit_id_single].update_unit_memory(self.status_old) # 原则上，有了后面的global communication之后，这里这个其实不是那么必要
            
            act_single = self.local_agent_dict[unit_id_single].step(status_single,unit_id_single)
            # 每一个都过滤一下，防止命令发岔了，这样才称得上健全。
            act_single_filtered = self.action_filter(act_single,[unit_id_single])

            self.act = self.act + act_single_filtered

        # 然后是global的，取出没被干扰的local的agent准备用来同步信息。只同步信息，不做决策。
        local_agent_unjammed = dict()
        for i in range(len(unit_ids_global)):
            unit_id_single = unit_ids_global[i]
            local_agent_unjammed[unit_id_single] = self.local_agent_dict[unit_id_single]

        # 然后是global的，通信未被干扰的情况，能够共享态势，互相传输命令。
        self.global_agent.num = self.num # 当前推演进程应该同步到各个装备上，global的也要同步
        act_global = self.global_agent.step(status)
        self.global_agent.communication(local_agent_unjammed) # 这个函数内部支持自定义，用来向没有受到干扰的local发额外的指令。
        act_global_filtered = self.action_filter(act_global, unit_ids_global)
        self.act = self.act + act_global_filtered
        
        self.status_old = copy.deepcopy(self.status)
        return  self.act

    def status_filter(self,status):
        # 其实不用四个返回值，只用ID就已经包含了所有信息了，但是这里这么处理，用着能够方便点。
        status_global = dict()
        status_local_list = [] 
        unit_ids_global = [] 
        unit_ids_local = [] 

        # 具体得等平台来连起来之后再来实现，看到底哪些要传，哪些不传。
        # print("status_filter: unfinished yet")
        unit_id_list = list(status.keys())
        unit_id_list_filtered = self.unit_id_filter(unit_id_list) # 得做过滤和容错
        # for unit_id in self.unit_ID_list:
        for unit_id in unit_id_list_filtered:
            # 遍历我方每一个可命令的装备，看是不是被干扰了
            unit_single = status[unit_id]
            flag_jam = self.check_connect(unit_id,status=status)

            if flag_jam == True:
                # 那就是说这个装备吃了干扰了。
                unit_ids_local.append(unit_id)
                # 顺便给分割一个用于输入到state里面的那种格式的status。
                status_single = dict()
                status_single[unit_id] = unit_single
                status_local_list.append(status_single)
            else:
                # 那就是说这个装备没吃干扰
                unit_ids_global.append(unit_id)

                # 态势这里也进行相应的整理。
                status_global[unit_id] = unit_single
            
        return status_global, status_local_list, unit_ids_global, unit_ids_local
    
    def action_filter(self, act_global, unit_ids_global):
        # 保险起见，对global agent给出的动作做出过滤。
        action_filtered = [] 
        for act_single in act_global:
            # 对每一条命令，检测是不是合法，不合法的就不要了。
            if "Id" in act_single:
                id_single = act_single["Id"]
            elif "tankid" in act_single:
                id_single =  act_single["tankid"]
            elif "ID" in act_single:
                id_single =  act_single["ID"]
            else:
                raise Exception("invalid id in action, please check.")
            if id_single in unit_ids_global:
                # 这个就是能通联的，所以这条就可以要了。
                action_filtered.append(act_single)
        
        return action_filtered        
     
    def check_connect(self,unit_id:str, **kargs):
        # 这个是为了方便封装一下，检测给过来的态势中，这个id的装备，到底是通联了还是没有。
        if "status" in kargs:
            status = kargs["status"]
        else:
            status = self.status 
        
        try:
            unit_single = status[unit_id]
        except:
            raise Exception("check_connect: stauts and unit_id seems not match, G!")
        # flag_jam = unit_single["isElectronicOn"] # 不是这个关键词，但是想要的关键词找不到，回头得问问阳哥。
        try:
            flag_jam=unit_single["DetectorState"][0]["be_disturbed"]
        except:
            flag_jam=False # 做一些容错。万一后世有什么奇奇怪怪的unit进来了，也不至于暴毙。
        ######################### 现在先来个盗版的，随机生成一些
        # if self.player=="red":
        #     self.num = status["redbmc3"]["simTime"]  # 这么玩儿才能读取到status_old
        # elif self.player=="blue":
        #     self.num = status["bluebmc3"]["simTime"]        
        # if self.num>5:
        #     if "Tank" in unit_id:
        #         flag_jam = True
        #     else:
        #         flag_jam = False 
        # else:
        #     flag_jam = False
        # print("check_connect: unfinished yet")
        ######################### 现在先来个盗版的，随机生成一些
        return flag_jam

        

    def check_update_local(self, unit_id, status_old):
        # 如果这个装备上一帧是通联的，这一帧是不通联的，则返回True，说明需要更新态势。
        # 反之，如果上一帧不通联，这一帧还是不通联，则说明不应该给它更新态势。
        flag_jam_before = self.check_connect(unit_id, status=status_old)
        flag_jam_now = self.check_connect(unit_id,status=self.status)
        
        flag_update = False 
        if (flag_jam_now==True) and (flag_jam_before==False):
            # 这一帧开始被干扰，所以需要更新一下局部的态势。
            flag_update = True
        elif (flag_jam_now==False) and (flag_jam_before==False):
            # 这一帧没有被干扰。道理上local agent确实能够拿到全局态势，但是反正也不调用local的东西，从程序优化的角度就不更新了
            # flag_update = True
            pass 
        elif (flag_jam_now==False) and (flag_jam_before==True):
            # 同上，从程序优化的角度就不更新了
            # flag_update = True
            pass 
        elif (flag_jam_now==True) and (flag_jam_before==True):
            # 一直在被干扰，那么拿不到新的全局态势，但是旧的是存着的。
            flag_update = False

        # print("check_update_local: unfinished yet")
        return flag_update

    def unit_id_filter(self,unit_id_list):
        # 暴力遍历一遍，看看那里面有的就拿出来，没有的就再说。
        unit_id_list_filtered = []
        for unit_id_single in unit_id_list:
            flag_valid = False 
            for name_single in self.name_list:
                if name_single in unit_id_single:
                    # 那就说明这个ID是合法的，需要对应一个local智能体。
                    flag_valid = True
                    break
            
            if flag_valid == True:
                # 那这个就是合法的，
                unit_id_list_filtered.append(unit_id_single)
            else:
                # 那这个就是不合法的，就过滤掉了。
                # 不是说真不合法，是说不需要对应一个local智能体。
                pass

        return unit_id_list_filtered

    def load_xlsx_deploy(self, xls_name=r'Deployment_ArmoredTruck_ZTL100'):
        # 这个是用来加载外部excel的，返回各种部署坐标。
        file_name = self.deploy_folder + "\\" + xls_name + ".xls"
        kaihuo_test_config_workbook = xlrd.open_workbook(file_name)
        kaihuo_test_config_sheets = kaihuo_test_config_workbook.sheets()
        kaihuo_test_config = kaihuo_test_config_sheets[0]._cell_values
        # geshu = len(kaihuo_test_config)
        return kaihuo_test_config

    def set_deploy_folder(self, xls_folder=r'E:\XXH\auto_test\guize\reddeploy'):
        if os.path.exists(xls_folder):
            self.deploy_folder = xls_folder
        else:
            raise Exception('XXHtest: invalid location, G!')
        pass

    def deploy(self,ids):
        # 这个也是延续之前的部署方式了。为了尽量减少依赖项保持稳定，发布版的部署坐标硬编码在程序里，而不再读取外部东西
        # 并把代码相应地简化一下，尝试减少行数增加可读性。
        deploy_type_dict = dict() # key:type, value, unit number
        building_loaction_list = [] 
        building_loaction_list.append([100.137777,13.6442,0])
        building_loaction_list.append([100.1167513,13.6432282,0])
        building_loaction_list.append([100.1644399,13.65847,0])
        building_loaction_list.append([100.103974397,13.63564213,0])
        building_loaction_list.append([100.140676439,13.607695814,0])
        

        if self.player == "red":
            # 那就说明现在是红方，那就照着红方的来
            deploy_LLA = [100.15427471282, 13.60603147549, 0]
            
            deploy_type_dict["ArmoredTruck_ZTL100_"] = 2  # 由于平台配置里有的有下划线有的没有，这里也得这么来了保持一致
            # deploy_type_dict["missile_truck"] = 3
            deploy_type_dict["MainBattleTank_ZTZ100_"] = 4
            deploy_type_dict["Howitzer_C100_"] = 1
            deploy_type_dict["WheeledCombatTruck_ZB100_"] = 2
            deploy_type_dict["Infantry"] = 2
            deploy_type_dict["ShipboardCombat_plane"] = 1
            deploy_type_dict["RedCruiseMissile_"] = 2
            deploy_type_dict["JammingTruck_"] = 1

            fire_config_dict= dict() # 用这个可以定义部署时装甲单位的配弹量，确切地说，穿甲弹和高爆弹的比例。
            fire_config_dict["MainBattleTank"] = [30,30]
            fire_config_dict["ArmoredTruck"] = [0,0]
            fire_config_dict["WheeledCombatTruck"] = [0,0]
            fire_config_dict["Howitzer"] = [40, 40]

            # 然后根据上面的设定，来生成ID和命令
            for type_single in list(deploy_type_dict.keys()):
                # 红方先部署，甚至都不需要什么判断。
                number_single = deploy_type_dict[type_single]
                for i in range(number_single):
                    ID_str = type_single + str(i)
                    flag, ArmorCar_type = self.is_ArmorCar(ID_str)
                    if flag:
                        fire_config = fire_config_dict[ArmorCar_type]
                        self.global_agent._ArmorCar_Deploy_Action(ID_str, deploy_LLA[0], deploy_LLA[1], deploy_LLA[2], fire_config[0], fire_config[1])
                    else:
                        self.global_agent._Deploy_Action(ID_str, deploy_LLA[0], deploy_LLA[1], deploy_LLA[2])
                    if "CruiseMissile" in ID_str:
                        self.deploy_addition([ID_str],[deploy_LLA])


        elif self.player == "blue":
            # 那就说明现在是蓝方，那就照着蓝方的来 
            deploy_LLA = [100.12472961, 13.66152304, 0]
            # deploy_type_dict["ArmoredTruck_ZTL200ID_"] = 2  # 由于平台配置里有的有下划线有的没有，这里也得这么来了保持一致
            # deploy_type_dict["missile_truck"] = 3
            deploy_type_dict["MainBattleTank_ZTZ200_"] = 4
            # deploy_type_dict["Howitzer_C100_"] = 1
            deploy_type_dict["WheeledCmobatTruck_ZB200_"] = 4
            deploy_type_dict["Infantry"] = 4+3
            deploy_type_dict["ShipboardCombat_plane"] = 1
            deploy_type_dict["BlueCruiseMissile_"] = 2
            deploy_type_dict["JammingTruck_"] = 1     

            fire_config_dict = dict() # 用这个可以定义部署时装甲单位的配弹量，确切地说，穿甲弹和高爆弹的比例。
            fire_config_dict["MainBattleTank"] = [30,30]
            fire_config_dict["ArmoredTruck"] = [0,0]
            fire_config_dict["WheeledCombatTruck"] = [0,0]
            fire_config_dict["Howitzer"] = [40, 40]

            # 然后根据上面的设定，来生成ID和命令
            for type_single in list(deploy_type_dict.keys()):
                # 蓝方有几个index要修的。手动搞一下好了。
                if "missile_truck" in type_single:
                    index_delta = 3
                elif ("Infantry" in type_single) :
                    index_delta = 2
                elif ("ShipboardCombat_plane" in type_single) or ("JammingTruck_" in type_single):
                    index_delta = 1
                else:
                    index_delta = 0 
                
                number_single = deploy_type_dict[type_single]
                for i in range(number_single):
                    ID_str = type_single + str(i+index_delta)
                    flag, ArmorCar_type = self.is_ArmorCar(ID_str)
                    if flag:
                        fire_config = fire_config_dict[ArmorCar_type]
                        self.global_agent._ArmorCar_Deploy_Action(ID_str, deploy_LLA[0], deploy_LLA[1], deploy_LLA[2], fire_config[0], fire_config[1])
                    else:
                        if ("Infantry" in ID_str) and (i>=4):
                            # 蓝方守备部队，直接部署到建筑物上。
                            deploy_LLA_single = building_loaction_list[i-4]
                            self.global_agent._Deploy_Action(ID_str, deploy_LLA_single[0], deploy_LLA_single[1], deploy_LLA_single[2])
                        else:
                            # 蓝方机动部队，统一部署
                            self.global_agent._Deploy_Action(ID_str, deploy_LLA[0], deploy_LLA[1], deploy_LLA[2])
                    if "CruiseMissile" in ID_str:
                        self.deploy_addition([ID_str],[deploy_LLA])    

        self.act = self.deploy_missile_truck()
        self.act = self.global_agent.act
        return self.act            

    def deploy_missile_truck(self):
        # 根据红蓝方，改一下导弹车的部署。
        if self.player=="red":
            # 红方的导弹发射车部署到远一点的地方
            deploy_LLA = [100.15427471282, 13.60603147549, 0]
            L_rad_norm = 100000 / 6371000 # 放100km外，算是相对典型、偏近的距离。
            L_deg_norm =  L_rad_norm / np.pi * 180 # 概略计算了，先转化成经纬度再说
            LLA_num = 3 
            missile_deploy_LLA = [deploy_LLA[0] + L_deg_norm , deploy_LLA[1] - L_deg_norm, deploy_LLA[2]]

            for i in range(LLA_num):
                id_single = "missile_truck" + str(i)
                self.global_agent._Deploy_Action(id_single, missile_deploy_LLA[0], missile_deploy_LLA[1], missile_deploy_LLA[2])
            pass 

        elif self.player=="blue":
            # 蓝方的发射车（防空）部署到那个那个周围。还得检测一下是不是出去了。
            center_LLA = [100.12472961, 13.66152304, 0]
            L_rad_norm = 1800 / 6371000
            L_deg_norm =  L_rad_norm / np.pi * 180 # 概略计算了，先转化成经纬度再说
            LLA_list = [] 
            LLA_num = 5
            # 先随机产一些坐标。
            while(len(LLA_list)<LLA_num):
                theta_deg = random.randint(0, 360) # 角度
                theta_rad = theta_deg / 180 * np.pi
                L_bili = random.uniform(0.6,1) # 距离
                L_deg = L_bili * L_deg_norm

                new_LLA = [float(center_LLA[0] + np.cos(theta_rad) * L_deg),
                            float(center_LLA[1]+ np.sin(theta_rad) * L_deg), center_LLA[2]]
                if(new_LLA[1]>13.67248):
                    # 那就是随机出去了，不算，重来
                    pass 
                else:
                    # 那就还行，算的。
                    LLA_list.append(new_LLA)
            
            # 然后部署
            for i in range(LLA_num):
                id_single = "missile_truck" + str(i+3)
                LLA_single = LLA_list[i]
                self.global_agent._Deploy_Action(id_single, LLA_single[0], LLA_single[1], LLA_single[2])
            
            print("blue surface to air missiles ready. ")
            pass

        self.act = self.global_agent.act
        return self.act

    def is_ArmorCar(self, id_single):
        # 根据ID来看是不是装甲车辆。装甲车辆需要更多的部署参数。
        flag = False
        ArmorCar_type = "none"
        if "MainBattleTank" in id_single:
            flag = True
            ArmorCar_type = "MainBattleTank"
        # elif "ArmoredTruck" in id_single: # 照着去年的抄，抄出问题来了
        #     flag = True
        #     ArmorCar_type = "ArmoredTruck"
        # elif "WheeledCombatTruck" in id_single:
        #     flag = True
        #     ArmorCar_type = "WheeledCombatTruck"
        elif "Howitzer" in id_single:
            flag = True
            ArmorCar_type = "Howitzer"

        return flag, ArmorCar_type
    
    def deploy_test(self,ids):
        # 这个是读取表格然后部署。搞阳间一点，原则上测试和真用都可以使用这个架构。
        
        # 保持顺序的部署算子类型，以便调试。0909xxh
        ArmoredTruck_ZTL100ID = []
        missile_truckID = []
        MainBattleTank_ZTZ100ID = []
        Howitzer_C100ID = []
        WheeledCombatTruck_ZB100ID = []
        InfantryID = []
        ShipboardCombat_planeID = []
        WheeledCombatTruck_ZB200ID = []
        missile_truckID = []
        MainBattleTank_ZTZ200ID = []
        InfantryID = []
        CruiseMissileID = [] 
        JammingTruckID = [] 

        # 加载各种装备的坐标
        if self.player == "red":
            Deployment_MainBattleTank_ZTZ100 = self.load_xlsx_deploy("Deployment_MainBattleTank_ZTZ100")
            Deployment_ArmoredTruck_ZTL100 = self.load_xlsx_deploy("Deployment_ArmoredTruck_ZTL100")
            Deployment_WheeledCombatTruck = self.load_xlsx_deploy("Deployment_WheeledCombatTruck")
            Deployment_Howitzer_C100 = self.load_xlsx_deploy("Deployment_Howitzer_C100")
            Deployment_missile_truck = self.load_xlsx_deploy("Deployment_missile_truck")
            Deployment_Infantry = self.load_xlsx_deploy("Deployment_Infantry")
            Deployment_ShipboardCombat_plane = self.load_xlsx_deploy("Deployment_ShipboardCombat_plane")    
            Deployment_CruiseMissile = self.load_xlsx_deploy("Deployment_CruiseMissile")
            Deployment_JammingTruck = self.load_xlsx_deploy("Deployment_JammingTruck")

            for i in range(len(Deployment_ArmoredTruck_ZTL100)):  # 确定序号以测试开火。
                ArmoredTruck_ZTL100ID.append("ArmoredTruck_ZTL100_" + str(i))
            for i in range(len(Deployment_MainBattleTank_ZTZ100)):  # 确定序号以测试开火。
                MainBattleTank_ZTZ100ID.append("MainBattleTank_ZTZ100_" + str(i))
            for i in range(len(Deployment_missile_truck)):  # 确定序号以测试开火。
                missile_truckID.append("missile_truck" + str(i))
            for i in range(len(Deployment_Howitzer_C100)):
                Howitzer_C100ID.append("Howitzer_C100_"+str(i))
            for i in range(len(Deployment_WheeledCombatTruck)):
                WheeledCombatTruck_ZB100ID.append("WheeledCmobatTruck_ZB100_"+str(i))
            for i in range(len(Deployment_Infantry)):
                # InfantryID.append("Infantry_"+str(i))
                InfantryID.append("Infantry" + str(i))
            for i in range(len(Deployment_ShipboardCombat_plane)):
                ShipboardCombat_planeID.append("ShipboardCombat_plane"+str(i))
            for i in range(len(Deployment_CruiseMissile)):
                CruiseMissileID.append("RedCruiseMissile_" + str(i))
            # CruiseMissileID.append("RedCruiseMissile")
            JammingTruckID.append("JammingTruck_0")
        elif self.player == "blue":
            Deployment_MainBattleTank_ZTZ200 = self.load_xlsx_deploy("Deployment_MainBattleTank_ZTZ200")
            Deployment_WheeledCombatTruck_ZB200 = self.load_xlsx_deploy("Deployment_WheeledCombatTruck_ZB200")
            Deployment_missile_truck = self.load_xlsx_deploy("Deployment_missile_truck")
            Deployment_Infantry = self.load_xlsx_deploy("Deployment_Infantry")
            Deployment_HeavyDestroyer_ShipID = []
            Deployment_CruiseMissile = self.load_xlsx_deploy("Deployment_CruiseMissile")
            Deployment_JammingTruck = self.load_xlsx_deploy("Deployment_JammingTruck")

            # 蓝方的
            for i in range(16):  # 确定序号以测试开火。
                MainBattleTank_ZTZ200ID.append("MainBattleTank_ZTZ200_" + str(i))
            for i in range(len(Deployment_missile_truck)):  # 确定序号以测试开火。
                missile_truckID.append("missile_truck" + str(i+2)) # 这个是红蓝方混编的。麻了。要根据json改。
            for i in range(len(Deployment_WheeledCombatTruck_ZB200)):
                WheeledCombatTruck_ZB200ID.append("WheeledCmobatTruck_ZB200_"+str(i))
            for i in range(len(Deployment_Infantry)):
                InfantryID.append("Infantry" + str(i+2))
            for i in range(len(Deployment_CruiseMissile)):
                CruiseMissileID.append("BlueCruiseMissile_"+str(i))
            # CruiseMissileID.append("BlueCruiseMissile")
            JammingTruckID.append("JammingTruck_1")

        # 然后开始真正的部署了，其实可以一波直接部署完了，但是尊重历史定制，还是分红蓝方来部署比较好。
        if self.player == "red":
            # 那就部署红方的东西。

            try:
                # 配合自动调试的修改，xxh0909
                Deployment_MainBattleTank_ZTZ100, Deployment_ArmoredTruck_ZTL100, Deployment_WheeledCombatTruck, \
                Deployment_Howitzer_C100, Deployment_missile_truck, Deployment_Infantry, Deployment_ShipboardCombat_plane \
                = self.deploy_modify_location(Deployment_MainBattleTank_ZTZ100, Deployment_ArmoredTruck_ZTL100, Deployment_WheeledCombatTruck, \
                Deployment_Howitzer_C100, Deployment_missile_truck, Deployment_Infantry, Deployment_ShipboardCombat_plane)
            except:
                print("XXHtest: auto kaihuo test disabled")

            # 然后开始部署了
            for i in range(len(MainBattleTank_ZTZ100ID)):  #8坦克
                self.global_agent._ArmorCar_Deploy_Action(MainBattleTank_ZTZ100ID[i], Deployment_MainBattleTank_ZTZ100[i][0],
                                                    Deployment_MainBattleTank_ZTZ100[i][1],
                                                    Deployment_MainBattleTank_ZTZ100[i][2], Deployment_MainBattleTank_ZTZ100[i][3],
                                                    Deployment_MainBattleTank_ZTZ100[i][4]
                                                            )
                # self.global_agent._Move_Action(MainBattleTank_ZTZ100ID[i],  Deployment_MainBattleTank_ZTZ100[i][0] + 0.0002,
                #                                     Deployment_MainBattleTank_ZTZ100[i][1] + 0.0002,
                #                                     Deployment_MainBattleTank_ZTZ100[i][2])

            for i in range(len(ArmoredTruck_ZTL100ID)):  #8装甲无人战车
                self.global_agent._Deploy_Action(ArmoredTruck_ZTL100ID[i], Deployment_ArmoredTruck_ZTL100[i][0],
                                                    Deployment_ArmoredTruck_ZTL100[i][1],
                                                    Deployment_ArmoredTruck_ZTL100[i][2])
                
                # self.global_agent._Move_Action(
                #     ArmoredTruck_ZTL100ID[i], Deployment_ArmoredTruck_ZTL100[i][0] + 0.0002,
                #                                     Deployment_ArmoredTruck_ZTL100[i][1] + 0.0002,
                #                                     Deployment_ArmoredTruck_ZTL100[i][2]
                # )


            for i in range(len(WheeledCombatTruck_ZB100ID)):  #8轻型装甲车Deployment_WheeledCombatTruck
                self.global_agent._Deploy_Action(WheeledCombatTruck_ZB100ID[i], Deployment_WheeledCombatTruck[i][0],
                                                    Deployment_WheeledCombatTruck[i][1],
                                                    Deployment_WheeledCombatTruck[i][2])
                
                # self.global_agent._Move_Action(
                #     WheeledCombatTruck_ZB100ID[i], Deployment_WheeledCombatTruck[i][0] + 0.0002,
                #                                     Deployment_WheeledCombatTruck[i][1] + 0.0002,
                #                                     Deployment_WheeledCombatTruck[i][2]
                # )


            for i in range(len(Howitzer_C100ID)):
                self.global_agent._ArmorCar_Deploy_Action(Howitzer_C100ID[i], Deployment_Howitzer_C100[i][0],
                                                    Deployment_Howitzer_C100[i][1],
                                                    Deployment_Howitzer_C100[i][2],
                                    Deployment_Howitzer_C100[i][3],
                                    Deployment_Howitzer_C100[i][4],
                                    )
            for i in range(len(ShipboardCombat_planeID)):
                self.global_agent._Deploy_Action(ShipboardCombat_planeID[i], Deployment_ShipboardCombat_plane[i][0],
                                                    Deployment_ShipboardCombat_plane[i][1],
                                                    Deployment_ShipboardCombat_plane[i][2],
                                    )


            for i in range(len(missile_truckID)):  #8导弹发射车
                if missile_truckID[i] != "":
                    self.global_agent._Deploy_Action(missile_truckID[i], Deployment_missile_truck[i][0],
                                                    Deployment_missile_truck[i][1],
                                                    Deployment_missile_truck[i][2]
                                        )
            for i in range(len(InfantryID)):  #8个步兵班
                self.global_agent._Deploy_Action(InfantryID[i], Deployment_Infantry[i][0],
                                                    Deployment_Infantry[i][1],
                                                    Deployment_Infantry[i][2]
                                    )
            
            for i in range(len(CruiseMissileID)): # 尝试搞点巡飞弹。
                self.global_agent._Deploy_Action(CruiseMissileID[i], Deployment_CruiseMissile[i][0],
                                                    Deployment_CruiseMissile[i][1],
                                                    Deployment_CruiseMissile[i][2])
            for i in range(len(JammingTruckID)):# 尝试搞一些电子干扰的小车。
                self.global_agent._Deploy_Action(JammingTruckID[i], Deployment_JammingTruck[i][0],
                                                    Deployment_JammingTruck[i][1],
                                                    Deployment_JammingTruck[i][2])
        elif self.player =="blue":
            # 那就是蓝方的部署阶段了呢，给他冲了。


            # 配合自动调试的修改，xxh0909
            try:
                # 配合自动调试的修改，xxh0909
                Deployment_MainBattleTank_ZTZ200, Deployment_missile_truck, Deployment_WheeledCombatTruck_ZB200, \
                Deployment_Infantry, Deployment_HeavyDestroyer_ShipID \
                = self.deploy_modify_location(Deployment_MainBattleTank_ZTZ200, Deployment_missile_truck,Deployment_WheeledCombatTruck_ZB200,
                                            Deployment_Infantry, Deployment_HeavyDestroyer_ShipID)
            except:
                print("XXHtest: auto kaihuo test disabled")

            for i in range(len(MainBattleTank_ZTZ200ID)):
                self.global_agent._ArmorCar_Deploy_Action(MainBattleTank_ZTZ200ID[i], Deployment_MainBattleTank_ZTZ200[i][0],
                                                    Deployment_MainBattleTank_ZTZ200[i][1],
                                                    Deployment_MainBattleTank_ZTZ200[i][2], Deployment_MainBattleTank_ZTZ200[i][3],
                                                    Deployment_MainBattleTank_ZTZ200[i][4])

            for i in range(len(WheeledCombatTruck_ZB200ID)):
                self.global_agent._Deploy_Action(WheeledCombatTruck_ZB200ID[i], Deployment_WheeledCombatTruck_ZB200[i][0],
                                                    Deployment_WheeledCombatTruck_ZB200[i][1],
                                                    Deployment_WheeledCombatTruck_ZB200[i][2])
            for i in range(len(missile_truckID)):
                self.global_agent._Deploy_Action(missile_truckID[i], Deployment_missile_truck[i][0],
                                                    Deployment_missile_truck[i][1],
                                                    Deployment_missile_truck[i][2])
            for i in range(len(InfantryID)):
                self.global_agent._Deploy_Action(InfantryID[i], Deployment_Infantry[i][0],
                                                    Deployment_Infantry[i][1],
                                                    Deployment_Infantry[i][2])
            for i in range(len(CruiseMissileID)): # 尝试搞点巡飞弹。
                self.global_agent._Deploy_Action(CruiseMissileID[i], Deployment_CruiseMissile[i][0],
                                                    Deployment_CruiseMissile[i][1],
                                                    Deployment_CruiseMissile[i][2])
            for i in range(len(JammingTruckID)):# 尝试搞一些电子干扰的小车。
                self.global_agent._Deploy_Action(JammingTruckID[i], Deployment_JammingTruck[i][0],
                                                    Deployment_JammingTruck[i][1],
                                                    Deployment_JammingTruck[i][2])
        else:
                raise Exception("player undefined in agent_dispatch")
        
        # 然后把阳哥之前弄的那个修正挪过来,就是初始要给一个move
        self.deploy_addition(CruiseMissileID,Deployment_CruiseMissile)

        self.act = self.global_agent.act
        return self.act
    
    def deploy_addition(self,CruiseMissileID,Deployment_CruiseMissile):
        # 这个最开始是用来处理巡飞弹的，让它开局直接能够飞起来。阳哥的原版方案是直接硬编码在python里，我觉着不彳亍。
        for i in range(len(CruiseMissileID)):
            rand_angle = random.randint(0,360)
            rand_angle_rad = rand_angle / 180 * np.pi # 来个随机方向。
            dl = 0.001 
            self.global_agent._Move_Action(CruiseMissileID[i], Deployment_CruiseMissile[i][0] + float(dl * np.cos(rand_angle_rad)),
                Deployment_CruiseMissile[i][1] + float(dl * np.sin(rand_angle_rad)),
                Deployment_CruiseMissile[i][2] + 114.514) 
        self.act = self.global_agent.act 
        return self.act

    def deploy_modify_location(self, *args):

        if self.deploy_modify_flag:
            # modify enabled
            print('red_agent: deploy_modify enabled')
            for i in range(len(self.name_list)):
                if self.name_list[i] in self.modify_unit_type:
                    for j in range(3):
                        args[i][0][j] = self.modify_location[j]
        return args
    
    def deploy_modify_set(self,my_unit_type, my_weapon_type, target_unit_type, location = [2.68, 39.70,0], index = 0,  **kargs):
        # 修改相应的东西的位置
        self.modify_unit_type = my_unit_type
        self.modify_location = location
        self.modify_index = index
        self.modify_weapon_type = my_weapon_type
        self.target_unit_type = target_unit_type

        self.deploy_modify_flag = True  # En Taro XXH!

        # 新加的，同步到global agent里面准备用于打炮。或者别的，总之往global里面同步测试信息的。
        test_config = {"my_unit_type" : my_unit_type , "my_weapon_type": my_weapon_type , "target_unit_type":target_unit_type, "location" : location, "index" : index }
        self.global_agent.load_test_config(test_config)
        self.global_agent.load_test_config(kargs)
        return 0
    
    def deploy_modify_getstate(self, state='stay'):
        # enum
        # VehicleMoveState
        # {
        #     move, // 移动
        # stay, // 停止
        # hidden // 掩蔽
        # offroad // 越野，
        # };
        self.modify_state = state
        
        # 这个也是，要多一层“传到global agent 里面去”的操作
        test_config = {"my_state": state}
        self.global_agent.load_test_config(test_config)
    
    def get_status(self):
        return self.status, self.global_agent.detected_state
    
    def set_commands(self, command_list:list):
        # print("set_commands: unfinished yet")
        # 首先把这些个command加入到queue里面去。增加一个键值对，当前时间。
        for comand_single in command_list:
            comand_single["step_num"] = self.num
            self.commands_queue.put(comand_single)
        
        # 然后开始执行，具体的逻辑还得想想。
        # 拿出第一个，如果是这一步的，就给它执行了，如果不是，就结束退出。
        # 2024，还得检测一下是不是通联的。有点重复计算也不管了，就这样了。
        status_global, status_local_list, unit_ids_global, unit_ids_local = self.status_filter(self.status)

        for i in range(114514): # 原则上这里应该是个while，但是保险起见防止死循环。
            if len(self.commands_queue.queue)==0:
                return # 没有什么命令，直接溜了溜了。
        
            # 看一下第一个
            comand_single = self.commands_queue.queue[0]
            if comand_single["step_num"] <= self.num:
                obj_id = comand_single["obj_id"]
                if obj_id in unit_ids_global:
                    # 执行
                    comand_single = self.commands_queue.get()
                    self.set_commands_single(comand_single)

        pass

    def set_commands_single(self,comand_single):
        # 这个是真的要开始解析命令了。
        obj_id = comand_single["obj_id"]
        if comand_single["type"] == "move":
            target_LLA = [comand_single['x'], comand_single['y'], 0 ] 
            if "WheeledCmobatTruck_ZB100" in obj_id:
                # 说明是步战车，步战车要走接兵的逻辑。
                for i in range(5): # 丑陋的字符串拼接操作，毫无通用性可言，鉴定为拉。
                    if ("_"+str(i)) in obj_id:
                        # 说明就是这个编号，
                        bing_id = "Infantry" + str(i)
                        self.global_agent.set_charge_and_xiache(obj_id, bing_id, target_LLA)
            elif "Infantry" in obj_id:
                # 步兵的话就是前面一定步数不做行动，后面再做行动。或者说，正在等上车的话就不做行动。
                for i in range(5): # 丑陋的字符串拼接操作，毫无通用性可言，鉴定为拉。
                    if str(i) in obj_id:
                        # 说明对应的是这个车。
                        che_id = "WheeledCmobatTruck" + "_ZB100_"+str(i)
                        try:
                            if self.global_agent.abstract_state[che_id]["abstract_state"] == "charge_and_xiache":
                                self.global_agent.set_none(obj_id)
                            else:
                                # 那就是说现在不需要上下车，那就冲。
                                self.global_agent.set_move_and_attack(obj_id, target_LLA)
                        except:
                            # 这里这个异常处理是为了防止复盘的时候跑出来的结果由于随机性导致不一样导致复盘命令变化
                            pass 
                    else:
                        # 说明对应的不是这个车，那就无事发生。
                        pass 
            else:
                # 除了车和步兵以外的情况，那就走呗，move。            
                self.global_agent.set_move_and_attack(obj_id, target_LLA)             
        elif comand_single["type"] == "stop":
            self.global_agent.set_open_fire(comand_single["obj_id"])
            # self.set_stop(comand_single["obj_id"])
            pass 
        elif comand_single["type"] == "off_board":
            # 这里要投机取巧了，不想新加抽象状态了，而是在当前抽象状态的基础上直接改变量。
            if "WheeledCmobatTruck" in obj_id:
                target_LLA = self.global_agent.__get_LLA(obj_id)
                if "next" in self.global_agent.abstract_state[obj_id]:
                    if self.global_agent.abstract_state[obj_id]["next"]["abstract_state"] == "charge_and_xiache":
                        # 另一种情况。其实这个应该是更广泛的情况。它在走，但是charge_and_xiache是在next里面。
                        self.global_agent.__finish_abstract_state(obj_id)
                if self.global_agent.abstract_state[obj_id]["abstract_state"] == "charge_and_xiache":
                    # 改抽象状态，让它觉得现在可以下车了，从而实现下车。
                    self.global_agent.abstract_state[obj_id]["target_LLA"] = target_LLA
                    self.global_agent.abstract_state[obj_id]["flag_state"] = 3
                
        else:
            raise Exception("undefined comand type in set_commands_single, G.")
        
if __name__ == "__main__":
    print("这个没法单独测试，构筑单独测试用例的意义也不是很大。直接去main.py里面测可也")