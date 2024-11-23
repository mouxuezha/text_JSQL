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
            local_agent_single.group_A_gai_config = self.group_A_gai_config
        
        
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
            self.act = self.step_LLM(status)
            pass
        elif self.player == "blue":
            # 当前智能体是蓝方
            # self.act = self.step_blue_shishi1(status)
            # self.act = self.step_blue_shishi2(status)
            self.act = self.step_blue_shishi3(status)
            # self.act = self.step_blue_shangxiache(status)
            # self.act = self.step_LLM(status)
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
    

    # 以下是我们测试的时候用过的代码，可供各队参考
    def step_red_test_move(self, status):
        # 原来的没法用 还是得硬编码一个
        # my_unit_type = self.test_config["my_unit_type"]
        # myids = [my_unit_type + "_0" , my_unit_type + "_1", my_unit_type + "_2", my_unit_type + "_3"]
        # target_location = self.test_config["target_location"]
        # for uid in myids:
        target_location =  [100.137163, 13.642893, 0]
        myids =  ["MainBattleTank_ZTZ100_0", "MainBattleTank_ZTZ100_1", "MainBattleTank_ZTZ100_2", "WheeledCmobatTruck_ZB100_0", "WheeledCmobatTruck_ZB100_1", "ArmoredTruck_ZTL100_0"]
        for uid in myids:
            self._Move_Action(uid, target_location[0], target_location[1], target_location[2])
        return self.act
    def step_blue_test_move(self, status):
        target_location =  [100.137163, 13.642893, 0]
        myids =  ["MainBattleTank_ZTZ200_0", "MainBattleTank_ZTZ200_1", "MainBattleTank_ZTZ200_2", "WheeledCmobatTruck_ZB200_0", "WheeledCmobatTruck_ZB200_1", ]
        for uid in myids:
            self._Move_Action(uid, target_location[0], target_location[1], target_location[2])
        return self.act

    def step_red_test_kaihuo(self,status):
        # 这个是用于测试开火的，这边要打炮。
        # _Attack_Action(self, Id, lon, lat, alt, Unit_Type)
        my_unit_type = self.test_config["my_unit_type"]
        my_id = my_unit_type + "_0"
        if "nfantry" in my_unit_type:
            my_id = my_unit_type  + "0"
        if "missile" in my_unit_type:
            my_id = my_unit_type  + "0"
        
        target_location = self.test_config["target_location"]
        weapon_type = self.test_config["my_weapon_type"] 

        # 然后就可以开始开火了
        # # 测一下Move
        # self._Move_Action(my_id,  target_location[0], target_location[1], target_location[2])
        if self.num>5:
            self._Attack_Action(my_id, target_location[0], target_location[1], target_location[2], weapon_type)
        return self.act
    
    def step_blue_test_kaihuo(self, status):
        # 这个是用于配合测试开火的。先固定，然后动起来。
        my_state = self.test_config["my_state"]
        my_unit_type = self.test_config["my_unit_type"]
        my_id = my_unit_type + "_0"
        if "nfantry" in my_unit_type:
            my_id = my_unit_type  + "2"
        if "missile" in my_unit_type:
            my_id = my_unit_type  + "3"
        
        my_LLA = self.get_LLA(my_id)
        location = self.test_config["location"]
        #_Move_Action(self, Id, lon, lat, alt)
        if my_state == "move":
            # 搞专业一点，在两个点位之间走来走去。
            # zuo_location = copy.deepcopy(my_LLA)
            # you_location = copy.deepcopy(my_LLA)
            zuo_location = copy.deepcopy(location) # 哪怕开始部署的地方有点问题，也得是按照这个走，才称得上是健全。
            you_location = copy.deepcopy(location)
            zuo_location[0] = zuo_location[0] - 0.001 
            you_location[0] = you_location[0] + 0.001
            jvli_zuo = self.distance(zuo_location[0], zuo_location[1], zuo_location[2],
                                 my_LLA[0], my_LLA[1], my_LLA[2])
            jvli_you = self.distance(you_location[0], you_location[1], you_location[2],
                                 my_LLA[0], my_LLA[1], my_LLA[2])
            if jvli_zuo<20:
                self._Move_Action(my_id,you_location[0], you_location[1], you_location[2] )
            elif jvli_you<20:
                self._Move_Action(my_id,zuo_location[0], zuo_location[1], zuo_location[2])
            elif abs(jvli_zuo-jvli_you)<200 and self.num<5:
                # 启动一下,如果在中间就往两边去。
                self._Move_Action(my_id,you_location[0], you_location[1], you_location[2] )

        elif my_state == 'stay':
            print("XXHtest: blue stay")
            self._Change_State(my_id,my_state)
        elif my_state == 'hidden':
            print("XXHtest: blue hidden")
            self._Change_State(my_id, my_state)
        return self.act
    
    def step_red_test_ganrao(self, status):
        # 这个是用来配合测试的，开干扰看对面有没有动静。
        ganrao_id = "JammingTruck_0"
        if self.num==5:
            # 开起来看看成色。
            self.act.append(self._SetJammer_Action(ganrao_id, 2))  # 当前仅开放该模式
        elif self.num==25:
            # 关了一下。
            self.act.append( self._SetJammer_Action(ganrao_id, 0)) # 改回去应该就是
        return self.act
    
    def step_blue_test_ganrao(self, status):
        # 这个也是用来配合测试的，开干扰之后先看状态。
        ganrao_id = "JammingTruck_1"
        if self.num==255:
            # 开起来看看成色。
            self.act.append(self._SetJammer_Action(ganrao_id, 2)) # 当前仅开放该模式
        return self.act
    
    def step_red_test_xunfeidan(self,status):
        # 这个是测试一下巡飞弹的攻击行不行，还要写一些毁伤。行了以后统一纳入到开火测试里里面
        xunfeidan_id = "RedCruiseMissile"
        if self.num == 5:
            # A一波看看成色。
            self._Attack_Action(xunfeidan_id, 100.137163+0.0001, 13.642893, 5, "CruiseMissile")
        return self.act

    def step_red_test_yueye(self, status):
        # 这个是先开状态转换然后让它进入到那里面
        # test_id = "MainBattleTank_ZTZ100_0"
        test_id = "Infantry0"
        target_location =  [100.137163+0.01, 13.642893, 0]
        if self.num>0 and self.num<3 :
            # 0为机动，1为静止，2为隐蔽，3为越野状态。
            self._Change_State(test_id,3)
        elif self.num >= 4: # 重复发命令便于调试
             self._Move_Action(test_id, target_location[0], target_location[1], target_location[2])
        return self.act
    
    def step_blue_test_building(self, status):
        # 这个是用来测试进房子的，后续还得测一下进房子之后的毁伤，得让它能吃到加成。
        test_id = "Infantry2"

        if self.num>2 and self.num<100:
            # 下达进房子的命令。0是出房子应该，1是进房子。vehicle_work_state = in_the_building;对应整数17
            self._PassInto_Action(test_id,1)
        elif self.num >= 100:
            self._PassInto_Action(test_id,0)
        

        return self.act
    # 以上是我们测试的时候用过的代码，可供各队参考

    def step_red_demo(self, status:dict):
        self.act = [] 
        # 示例，直接往上面冲就完事儿了。
        
        # 移动
        target_LLA = [100.137777, 13.6442, 0 ]
        ID_list = list(status.keys())
        # 上来先改成越野模式。
        if self.num == 1:
            for ID_single in ID_list:
                # self._Change_State(ID_single,3)      
                pass  
        if self.num == 11:
            for ID_single in ID_list:
                self._Move_Action(ID_single, target_LLA[0], target_LLA[1], target_LLA[2])
        
        # 侦察和打击
        # 获取探测信息测试
        detectinfo = self.get_detect_info(status)
        #分别获取蓝方ZB讯息
        detectedWheeledCmobatTruck_ZB200ID = [id for id in detectinfo.keys() if "WheeledCmobatTruck_ZB200" in id]
        detectedArmoredTruck_ZTL100ID = [id for id in detectinfo.keys() if "ArmoredTruck_ZTL100" in id]
        detectedMissleTruckID = [id for id in detectinfo.keys() if "missile_truck" in id]
        detectedInfantryID = [id for id in detectinfo.keys() if "Infantry" in id]
        detectedMainBattleTank_ZTZ200ID = [id for id in detectinfo.keys() if "MainBattleTank_ZTZ200" in id]
        detectedHowitzer_C100ID = [id for id in detectinfo.keys() if "Howitzer_C100" in id]
        detectedHeavyDestroyer_ShipID = [unit for unit in detectinfo.keys() if "HeavyDestroyer_Ship" in unit]

        #根据需求组合探测信息
        detectedArmored = detectedWheeledCmobatTruck_ZB200ID+detectedMissleTruckID+\
                          detectedMainBattleTank_ZTZ200ID
        # 申明弹种
        WheeledCmobatTruck_ZB100MissileType = ["Bullet_ZT"]
        ArmoredTruck_ZTL100MissileType = ["Bullet_ZT"]
        MissleTruckMissileType = ["ShortRangeMissile"]
        InfantryMissileType = ["RPG", "bullet"]
        MainBattleTank_ZTZ100MissileType = ["Bullet_ZT", "ArmorPiercingShot_ZT", "HighExplosiveShot_ZT"]
        Howitzer_C100MissileType = ["Bullet_ZT","ArmorPiercingShot", "HighExplosiveShot"]
        ShipboardCombat_planeMissileType = ["AGM"]        
        detectedAll = detectedInfantryID+detectedArmored

        unit_tanks = self.select_by_type("Tank")
        MainBattleTank_ZTZ100ID = list(unit_tanks.keys())
        unit_missile = self.select_by_type("missile_truck")
        missile_truckID = list(unit_missile.keys())
        if self.num >= 5:
            #用主Zh坦克打
            # for targetid in detectedAll:
            #     for equip in MainBattleTank_ZTZ100ID:
            #         if self.Weapon_estimate(status, equip, MainBattleTank_ZTZ100MissileType[2]):
            #             self._Attack_Action(equip, detectinfo[targetid]['targetLon'],
            #                                             detectinfo[targetid]['targetLat'],
            #                                             detectinfo[targetid]['targetAlt'],
            #                                             MainBattleTank_ZTZ100MissileType[2])  
            
            # 改进版
            for equip in MainBattleTank_ZTZ100ID:
                # 根据我方LLA，找一个最近的敌方，避免重复指令。
                my_LLA = self.get_LLA(equip,status=status)
                detectinfo = self._status_filter(detectinfo)
                targetid,jvli_nearest = self.get_nearest(my_LLA, detectinfo)
                if jvli_nearest<114514:
                    # if self.Weapon_estimate(status, equip, MainBattleTank_ZTZ100MissileType[2]):
                    #     self._Attack_Action(equip, detectinfo[targetid]['targetLon'],
                    #                                     detectinfo[targetid]['targetLat'],
                    #                                     detectinfo[targetid]['targetAlt'],
                    #                                     MainBattleTank_ZTZ100MissileType[2])  
                    if self.Weapon_estimate(status, equip, MainBattleTank_ZTZ100MissileType[1]):
                        self._Attack_Action(equip, detectinfo[targetid]['targetLon'],
                                                        detectinfo[targetid]['targetLat'],
                                                        detectinfo[targetid]['targetAlt'],
                                                        MainBattleTank_ZTZ100MissileType[1])

        if self.num >=500:
            # 发挥红方火力优势。
            for equip in missile_truckID:
                my_LLA = self.get_LLA(equip,status=status)
                detectinfo = self._status_filter(detectinfo)
                targetid,jvli_nearest = self.get_nearest(my_LLA, detectinfo)    
                if jvli_nearest<1145141919:            
                    if self.Weapon_estimate(status, equip, MissleTruckMissileType[0]):
                        self._Attack_Action(equip, detectinfo[targetid]['targetLon'],
                                                        detectinfo[targetid]['targetLat'],
                                                        detectinfo[targetid]['targetAlt'],
                                                        MissleTruckMissileType[0]) 
            
        return self.act

    def step_blue_demo(self, status:dict):
        self.act = [] 
        # 也是直接冲
        target_LLA = [100.137777, 13.6442, 0 ]
        ID_list = list(status.keys())

        if self.num == 2:
            for ID_single in ID_list:
                # self._Change_State(ID_single,3)
                pass
            # 上下车演示：
            for i in range(4):
                IFV_ID = "WheeledCmobatTruck_ZB200_" + str(i)
                infantry_ID = "Infantry" + str(i+2)
                self._On_Board_Action(IFV_ID, infantry_ID)  

        if self.num == 21:
            for ID_single in ID_list:
                self._Move_Action(ID_single, target_LLA[0], target_LLA[1], target_LLA[2])       

        # 侦察和打击
        # 获取探测信息测试
        detectinfo = self.get_detect_info(status)
        #分别获取蓝方ZB讯息
        detectedWheeledCmobatTruck_ZB100ID = [id for id in detectinfo.keys() if "WheeledCmobatTruck_ZB100" in id]
        detectedArmoredTruck_ZTL100ID = [id for id in detectinfo.keys() if "ArmoredTruck_ZTL100" in id]
        detectedMissleTruckID = [id for id in detectinfo.keys() if "missile_truck" in id]
        detectedInfantryID = [id for id in detectinfo.keys() if "Infantry" in id]
        detectedMainBattleTank_ZTZ100ID = [id for id in detectinfo.keys() if "MainBattleTank_ZTZ100" in id]
        detectedHowitzer_C100ID = [id for id in detectinfo.keys() if "Howitzer_C100" in id]
        detectedHeavyDestroyer_ShipID = [unit for unit in detectinfo.keys() if "HeavyDestroyer_Ship" in unit]

        #根据需求组合探测信息
        detectedArmored = detectedArmoredTruck_ZTL100ID +detectedWheeledCmobatTruck_ZB100ID + detectedMissleTruckID + detectedMainBattleTank_ZTZ100ID + detectedHowitzer_C100ID
        # 申明弹种
        WheeledCmobatTruck_ZB100MissileType = ["Bullet_ZT"]
        ArmoredTruck_ZTL100MissileType = ["Bullet_ZT"]
        MissleTruckMissileType = ["ShortRangeMissile"]
        InfantryMissileType = ["RPG", "bullet"]
        MainBattleTank_ZTZ100MissileType = ["Bullet_ZT", "ArmorPiercingShot_ZT", "HighExplosiveShot_ZT"]
        Howitzer_C100MissileType = ["Bullet_ZT","ArmorPiercingShot", "HighExplosiveShot"]
        ShipboardCombat_planeMissileType = ["AGM"]     
        WheeledCmobatTruck_ZB200MissileType = ["Bullet_ZT"]
        MissleTruckMissileType = ["ShortRangeMissile"]
        InfantryMissileType = ["RPG", "bullet"]
        MainBattleTank_ZTZ200MissileType = ["Bullet_ZT", "ArmorPiercingShot_ZT", "HighExplosiveShot_ZT"]   
        
        detectedAll = detectedInfantryID+detectedArmored

        unit_tanks = self.select_by_type("Tank")
        MainBattleTank_ZTZ200ID = list(unit_tanks.keys())
        if self.num >= 5:
            #用主Zh坦克打
            for equip in MainBattleTank_ZTZ200ID:
                # 根据我方LLA，找一个最近的敌方，避免重复指令。
                my_LLA = self.get_LLA(equip,status=status)
                detectinfo = self._status_filter(detectinfo)
                targetid,jvli_nearest = self.get_nearest(my_LLA, detectinfo)
                if jvli_nearest<114514:
                    for equip in MainBattleTank_ZTZ200ID:
                        if self.Weapon_estimate(status, equip, MainBattleTank_ZTZ200MissileType[1]):
                            self._Attack_Action(equip, detectinfo[targetid]['targetLon'],detectinfo[targetid]['targetLat'],detectinfo[targetid]['targetAlt'],MainBattleTank_ZTZ200MissileType[1])  
                        # if self.Weapon_estimate(status, equip, MainBattleTank_ZTZ200MissileType[2]):
                        #     self._Attack_Action(equip, detectinfo[targetid]['targetLon'],detectinfo[targetid]['targetLat'],detectinfo[targetid]['targetAlt'],MainBattleTank_ZTZ200MissileType[2])  
        if self.num == 500:
            # 电磁干扰效果展示。
            ganrao_id = "JammingTruck_1"
            self._SetJammer_Action(ganrao_id, 2)          
        return self.act 
    
    def step_red_shishi1(self, status:dict):
        self.act = [] 
        blue_deploy_LLA = [100.12472961, 13.66152304, 0]
        # 先把兵种的分类做了
        bin_status = self.select_by_type("Infantry")
        tank_status = self.select_by_type("MainBattleTank")
        xiaoche_status = self.select_by_type("ArmoredTruck")
        che_status = self.select_by_type("WheeledCmobatTruck")
        feiji_status = self.select_by_type("ShipboardCombat_plane")
        xunfeidan_status = self.select_by_type("CruiseMissile")
        daodan_status = self.select_by_type("missile_truck")
        pao_status = self.select_by_type("Howitzer")
        ganraoche_status = self.select_by_type("JammingTruck")
        base_LLA = self.building_loaction_list[0]

        if self.num<=1:
            # 还是搞个初始化好了。
            self.Inint_abstract_state(status)

        if self.num ==1:
            self.set_UAV_scout(feiji_status,blue_deploy_LLA,R=4500)
            self.set_UAV_scout(xunfeidan_status,"ShipboardCombat_plane0",R=500)
            self.set_none(daodan_status) # 这个是导弹先不慌开火
            # self.set_open_fire(daodan_status) # 新版的这个里面也自带了导弹不慌开火。
        
        # if self.num == 11:
            
        #     # self.group_A_gai(base_LLA, status=(tank_status | che_status | xiaoche_status))
        #     # self.group_A(base_LLA, status=(tank_status | che_status | xiaoche_status))
        #     self.group_A(base_LLA, status=tank_status)
        #     pass

        # 先搞一个最挫的红方绕路偷家打法，从左边绕
        LLA_list = []
        LLA_list.append([100.096, 13.6109, 0])
        LLA_list.append([100.092, 13.6463, 0])
        LLA_list.append([100.12472961, 13.66152304, 0])
        if self.num ==2: # 开局反正不会被干扰，不用那啥。
            self.group_A2(LLA_list[1], che_status, bin_status)
            # self.group_A(LLA_list[0],status=(tank_status | xiaoche_status  | ganraoche_status))
            self.group_A(LLA_list[0],status=(tank_status | xiaoche_status | pao_status | ganraoche_status))
            # self.group_A([100.104,13.6389,0],status=(xiaoche_status))
        
        # if (self.num >= 500) and (self.num <= 1500) and (self.num%11==0):
        if self.num == 300:
            # 其实被干扰了也没啥，反正只要通信恢复就会自动同步过去的哇。
            # self.group_A(LLA_list[1],status=(xiaoche_status))
            self.group_A([100.104,13.6389,0],status=(xiaoche_status))

            
        if self.num in [600,610,620]:
            # 其实被干扰了也没啥，反正只要通信恢复就会自动同步过去的哇。
            # self.group_A(LLA_list[1],status=(tank_status | pao_status | ganraoche_status))
            self.group_A(LLA_list[1],status=pao_status)
        if self.num in [680]:
            self.set_open_fire(pao_status)
        if self.num in [900,910,920]:
            self.group_A2(LLA_list[1], che_status, bin_status)
            # self.group_A(LLA_list[1],status=pao_status)
        if (self.num >= 1200) and (self.num %11==4):
            # self.group_A2(LLA_list[1], che_status, bin_status)
            # self.group_A(LLA_list[2],status=(tank_status | xiaoche_status | che_status |bin_status))
            self.group_A(LLA_list[2],status=(pao_status | xiaoche_status | che_status |bin_status))
            self.set_open_fire(pao_status)


        self.Gostep_abstract_state()
        # self._Move_Action("MainBattleTank_ZTZ100_0", base_LLA[0], base_LLA[1], base_LLA[2])
        return self.act 

    def step_red_shishi2(self, status:dict):
        # 红方相对主动，先从红方开始写好了。
        # 来点儿策略，说法就是先分散隐蔽，然后探到敌方主力在左边就往右边进攻，探到敌方主力在右边就往左边进攻。

        # 前面一些步数先分散
        # enemy_direction = "left" # or right
        
        if "direction_enemy" in self.red_step_config:
            # 如果是这个，那就说明是已经定出来敌人在哪儿了
            enemy_direction = self.red_step_config["direction_enemy"]
            flag_detected = True # False # 已经定出来了，后面不再更新了。
            # 这里其实等于true也无所谓，反正自己更新自己就是了，还可读性好一些。
        else:
            # 还没定出来，那就check一下。
            flag_detected, enemy_direction = self.check_enemy_direction2(self.detected_state2,[100.138,13.644,0])
        
        if (flag_detected == True or (self.num > 400 and not("direction_enemy" in self.red_step_config))) and (not "flag_initialized" in self.red_step_config):
            # 那就是开始行动,存一下全局变量。
            self.red_step_config["direction_enemy"] = enemy_direction
            self.red_step_config["num_relative"] = 0 # 跟庙算的时候类似的，来一个相对的步数，方便。
            self.red_step_config["flag_initialized"] = True # 得额外加一个标志位，不然就会在这里一直初始化，无法推进num_relative
            if enemy_direction == "right":
                # 敌方在右边，那么我方就从左边去。
                LLA_list = [] 
                LLA_list.append([100.096, 13.6109, 0])
                LLA_list.append([100.092, 13.6463, 0])
                LLA_list.append([100.114, 13.6308, 0]) # 榴弹炮卡射程炸房子的点
                LLA_list.append([100.12472961, 13.66152304, 0])# 蓝方老家
                
                num_list = [] 
                num_list.append(2)
                num_list.append(800)
                num_list.append(1200)
                num_list.append(1800)
            elif enemy_direction == "left":
                # 敌方在左边，那么我方就从右边去
                LLA_list = [] 
                LLA_list.append([100.182, 13.6347, 0])
                LLA_list.append([100.175, 13.6446, 0])
                LLA_list.append([100.167, 13.6472, 0]) # 榴弹炮卡射程炸房子的点
                # LLA_list.append([100.162, 13.6529, 0]) # 接近敌方房子的点。
                # LLA_list.append([100.12472961, 13.66152304, 0])# 蓝方老家
                LLA_list.append([100.138, 13.6605, 0]) # 最后的目标点，蓝方老家。但是蓝方老家过不去，所以是接近的地方。

                num_list = []                
                num_list.append(2)
                num_list.append(800)
                num_list.append(1200)
                num_list.append(1800)
            self.red_step_config["LLA_list"] = LLA_list
            self.red_step_config["num_list"] = num_list

        # 然后后面就开始决策了，如果已经判断出了敌人方向，就往反方向突击，如果没有判断出敌人的方向，就去一个比较好的位置等一下。
        if not ("direction_enemy" in self.red_step_config):
            # 那就是还没选定出击方向
            self.step_red_shishi2_waiting(status)
        else:
            # 那就是已经选定出击方向
            self.step_red_shishi2_moven(status)
        
        # 这句统一拿出来外面写了。
        self.Gostep_abstract_state()
        return self.act 
    
    def step_red_shishi2_waiting(self, status:dict):
        # 先A到那一片小区域的外边去，无人机啥的放出去侦查
        self.act = [] 
        blue_deploy_LLA = [100.12472961, 13.66152304, 0]
        # 先把兵种的分类做了
        bin_status = self.select_by_type("Infantry")
        tank_status = self.select_by_type("MainBattleTank")
        xiaoche_status = self.select_by_type("ArmoredTruck")
        che_status = self.select_by_type("WheeledCmobatTruck")
        feiji_status = self.select_by_type("ShipboardCombat_plane")
        xunfeidan_status = self.select_by_type("CruiseMissile")
        daodan_status = self.select_by_type("missile_truck")
        pao_status = self.select_by_type("Howitzer")
        ganraoche_status = self.select_by_type("JammingTruck")      

        if self.num<=1:
            # 还是搞个初始化好了。
            self.Inint_abstract_state(status)

        if self.num ==1:
            # 巡飞弹分开，一个一个用。
            xunfeidan_status1, xunfeidan_status2 = self.select_by_devide(xunfeidan_status)
            self.set_UAV_scout(feiji_status,blue_deploy_LLA,R=4500)
            self.set_UAV_scout(xunfeidan_status1,[100.116, 13.6432, 0],R=2000)
            self.set_UAV_scout(xunfeidan_status2,[100.153, 13.6499, 0],R=2000)
            # self.set_none(daodan_status) # 这个是导弹先不慌开火
            self.set_open_fire(daodan_status) # 新版的这个里面也自带了导弹不慌开火。

        if self.num ==2: 
            self.group_A2([100.141,13.6084,0], che_status, bin_status) # 步兵也开出去，放在房子旁边。
            self.group_A([100.149,13.6183,0],status=(tank_status | xiaoche_status | pao_status | ganraoche_status)) # 先过河，不要卡在这边。
            # self.group_A([100.104,13.6389,0],status=(xiaoche_status))            
        

        # print("unfinished yet")

    def step_red_shishi2_moven(self, status:dict):
        # 读取对应的点列和时间点，恐怕是比较好的。就不用写两个了。
        # 先A到那一片小区域的外边去，无人机啥的放出去侦查
        self.act = [] 
        blue_deploy_LLA = [100.12472961, 13.66152304, 0]
        # 先把兵种的分类做了
        bin_status = self.select_by_type("Infantry")
        tank_status = self.select_by_type("MainBattleTank")
        xiaoche_status = self.select_by_type("ArmoredTruck")
        che_status = self.select_by_type("WheeledCmobatTruck")
        feiji_status = self.select_by_type("ShipboardCombat_plane")
        xunfeidan_status = self.select_by_type("CruiseMissile")
        daodan_status = self.select_by_type("missile_truck")
        pao_status = self.select_by_type("Howitzer")
        ganraoche_status = self.select_by_type("JammingTruck")    

        # 然后从变量里面把进攻的路径点取出来。
        LLA_list = self.red_step_config["LLA_list"]
        num_list = self.red_step_config["num_list"]
        num_relative = self.red_step_config["num_relative"]

        if num_relative ==num_list[0]: 
            self.group_A2(LLA_list[0], che_status, bin_status)
            self.group_A(LLA_list[0],status=(tank_status | xiaoche_status | pao_status | ganraoche_status))
            
        if num_relative in [num_list[1],num_list[1]+10,num_list[1]+20]: # 这个是防干扰的小处理。
            # 其实被干扰了也没啥，反正只要通信恢复就会自动同步过去的哇。
            self.group_A(LLA_list[1],status=pao_status)
        if num_relative in [num_list[1] + 80]:
            self.set_open_fire(pao_status)

        if num_relative in [num_list[2],num_list[2]+10,num_list[2]+20]:
            self.group_A2(LLA_list[2], che_status, bin_status)
            self.group_A(LLA_list[2], status=( tank_status |pao_status | ganraoche_status| xiaoche_status))

        if (num_relative in [num_list[3],num_list[3]+10,num_list[3]+20]):
            self.group_A(LLA_list[3],status=( tank_status | xiaoche_status | che_status | bin_status  | ganraoche_status))
            self.set_open_fire(pao_status)

        num_relative = num_relative + 1
        self.red_step_config["num_relative"] = num_relative

        # print("unfinished yet")

    def step_red_shangxiache(self,status:dict):
        self.act= [] 
        # 这个也是为了配合来哥好好测上下车的。
        location_list = [] 
        location_list.append([100.154, 13.614, 0])
        location_list.append([100.161, 13.6028, 0])
        location_list.append([100.147, 13.6031, 0])
        # 先把兵种的分类做了
        bin_status = self.select_by_type("Infantry")
        tank_status = self.select_by_type("MainBattleTank")
        xiaoche_status = self.select_by_type("ArmoredTruck")
        che_status = self.select_by_type("WheeledCmobatTruck")
        feiji_status = self.select_by_type("ShipboardCombat_plane")
        xunfeidan_status = self.select_by_type("CruiseMissile")
        daodan_status = self.select_by_type("missile_truck")
        pao_status = self.select_by_type("Howitzer")
        ganraoche_status = self.select_by_type("JammingTruck")
        if self.num % 1200 == 2:
            # 那就去第一个点  
            index = 0 
        elif self.num % 1200 == 402:
            # 那就去第二个点
            index = 1
        elif self.num % 1200 == 802:
            # 那就去第三个点
            index = 2 
        else:
            # 那就不重复发命令了
            index = -1 

        if index>=0:
            target_LLA =  location_list[index]
            self.group_A2(target_LLA, che_status, bin_status)
        self.Gostep_abstract_state()
        # self._Move_Action("MainBattleTank_ZTZ100_0", base_LLA[0], base_LLA[1], base_LLA[2])
        return self.act 

    def step_red_xunfeidan(self,status:dict):
        # 这个是隔离出来测巡飞弹攻击的。
        # 先A到那一片小区域的外边去，无人机啥的放出去侦查
        self.act = [] 
        blue_deploy_LLA = [100.12472961, 13.66152304, 0]
        # 先把兵种的分类做了
        bin_status = self.select_by_type("Infantry")
        tank_status = self.select_by_type("MainBattleTank")
        xiaoche_status = self.select_by_type("ArmoredTruck")
        che_status = self.select_by_type("WheeledCmobatTruck")
        feiji_status = self.select_by_type("ShipboardCombat_plane")
        xunfeidan_status = self.select_by_type("CruiseMissile")
        daodan_status = self.select_by_type("missile_truck")
        pao_status = self.select_by_type("Howitzer")
        ganraoche_status = self.select_by_type("JammingTruck")      

        if self.num<=1:
            # 还是搞个初始化好了。
            self.Inint_abstract_state(status)

        if self.num ==1:
            # 巡飞弹分开，一个一个用。
            xunfeidan_status1, xunfeidan_status2 = self.select_by_devide(xunfeidan_status)
            self.set_UAV_scout(feiji_status,blue_deploy_LLA,R=4500)
            self.set_UAV_scout(xunfeidan_status1,[100.116, 13.6432, 0],R=2000)
            self.set_UAV_scout(xunfeidan_status2,[100.153, 13.6499, 0],R=1200)        
        
        self.Gostep_abstract_state()
        return self.act 
    def step_blue_shishi1(self,status:dict):
        self.act = [] 
        red_deploy_LLA = [100.15427471282, 13.60603147549, 0]
        blue_deploy_LLA = [100.12472961, 13.66152304, 0]
        # 先把兵种的分类做了
        bin_status = self.select_by_type("Infantry")
        bin1_status= dict()
        bin2_status = dict()
        bin_id_list = list(bin_status.keys())
        for i in range(len(bin_id_list)):
            if i <4:
                # 那就是机动步兵
                bin1_status[bin_id_list[i]] = bin_status[bin_id_list[i]]
            else:
                # 那就是驻防步兵
                bin2_status[bin_id_list[i]] = bin_status[bin_id_list[i]]
        tank_status = self.select_by_type("MainBattleTank")
        xiaoche_status = self.select_by_type("ArmoredTruck")
        che_status = self.select_by_type("WheeledCmobatTruck")
        feiji_status = self.select_by_type("ShipboardCombat_plane")
        ganraoche_status = self.select_by_type("JammingTruck")

        if self.num ==1:
            # 驻防步兵就开局直接进房子可也。
            self.set_hidden_and_alert(bin2_status)
            # 先知一飞开三矿
            self.set_UAV_scout(feiji_status,red_deploy_LLA,R=3000)
            # 干扰车冲一波看看成色。
            self.set_move_and_jammer(ganraoche_status, red_deploy_LLA, model=-1)
        
        if self.num >=2 and self.num < 2000:
            # 调一下态势认知的那些函数。# 0923好像不是太好使，这玩意check不出来。
            result_state_list, variance, index = self.check_enemy_group(self.detected_state2, R_threshold=1500)
            if variance>0.7:
                # 那就说明过来的敌方的集中程度比较高。那就合兵对付它。
                result_state = result_state_list[index]
                base_LLA = self.building_loaction_list[index]
                n_fangxiang = self.check_enemy_direction(result_state, base_LLA)
                # A过去还是可以做到的吧。
                # self.group_A(base_LLA, status=(tank_status | ganraoche_status))
                
                if self.num < 400:
                    self.group_A_gai(base_LLA, status=(tank_status ), vector=n_fangxiang)
                    # self.group_A_gai(base_LLA, status=(tank_status | ganraoche_status), vector=n_fangxiang)
                    # self.group_A(base_LLA,status=ganraoche_status)
                    self.group_A2(base_LLA-0.001*n_fangxiang, che_status, bin1_status)
                else:
                    # self.group_A_gai(base_LLA, status=(tank_status | ganraoche_status ), vector=n_fangxiang,name="blue2")
                    # self.group_A_gai(base_LLA, status=( che_status |bin1_status), vector=n_fangxiang,name="blue3")
                    # 上面这个不太对，会变成往侧面就去了，不知道为啥。
                    self.group_A(base_LLA, status=(tank_status | ganraoche_status ))
                    self.group_A(base_LLA, status=( che_status |bin1_status))
                pass
            else:
                # 那就说明过来的敌方比较分散，需要想一些办法来处理。
                print("unfinished yet in step_blue_shishi")
        if self.num > 2500:
            # 要是到最后几步了，就A到点里去好了。
            self.group_A(blue_deploy_LLA, status=( che_status |tank_status| ganraoche_status))    
            
        # 其他的，尝试搞一些博弈，比如侦测到对面从哪边过来，就相应地去防守那个方向。比如看见对面无人机过来了，就把干扰车开过去准备给它干扰了。原则上给它干扰了就能压制它传情报。由于开了干扰就全图可见，就还有分兵的说法。

        self.Gostep_abstract_state()
        return self.act  

    def step_blue_shishi2(self,status:dict):
        # 这个是用来确证“静止打运动、隐蔽打机动”能够出效果的，就是先A到红方shishi1的路上，然后隐蔽起来，实现一个以静打动，看看成色。
        self.act = [] 
        red_deploy_LLA = [100.15427471282, 13.60603147549, 0]
        blue_deploy_LLA = [100.12472961, 13.66152304, 0]
        # 先把兵种的分类做了
        bin_status = self.select_by_type("Infantry")
        bin1_status= dict()
        bin2_status = dict()
        bin_id_list = list(bin_status.keys())
        for i in range(len(bin_id_list)):
            if i <4:
                # 那就是机动步兵
                bin1_status[bin_id_list[i]] = bin_status[bin_id_list[i]]
            else:
                # 那就是驻防步兵
                bin2_status[bin_id_list[i]] = bin_status[bin_id_list[i]]
        tank_status = self.select_by_type("MainBattleTank")
        xiaoche_status = self.select_by_type("ArmoredTruck")
        che_status = self.select_by_type("WheeledCmobatTruck")
        feiji_status = self.select_by_type("ShipboardCombat_plane")
        ganraoche_status = self.select_by_type("JammingTruck")
        xunfeidan_status = self.select_by_type("CruiseMissile")
        
        base_LLA = self.building_loaction_list[2]
        base_LLA_gai = (np.array(base_LLA) - np.array(blue_deploy_LLA)) * 0.8  + np.array(blue_deploy_LLA)
        base_LLA_gai = list(base_LLA_gai)

        if self.num ==1:
            # 驻防步兵就开局直接进房子可也。
            self.set_hidden_and_alert(bin2_status)
            # 先知一飞开三矿
            self.set_UAV_scout(feiji_status,red_deploy_LLA,R=4000)
            self.set_UAV_scout(xunfeidan_status,base_LLA,R=1500)
            # 干扰车冲一波看看成色。
            self.set_move_and_jammer(ganraoche_status, red_deploy_LLA, model=-1)
        
        if self.num >=2 and self.num < 600 and self.num%10==2:
            # 调一下态势认知的那些函数。# 0923好像不是太好使，这玩意check不出来。
            # self.group_A_gai(base_LLA, status=(tank_status ))
            if self.num >=20:
                self.group_A_gai(base_LLA_gai, status=(tank_status | ganraoche_status))
            # self.group_A(base_LLA,status=ganraoche_status)
            self.group_A2(base_LLA, che_status, bin1_status)
            
        elif self.num == 620:
            # 切成隐蔽状态。
            status=(tank_status  | che_status | bin1_status)
            self.set_hidden_and_alert(status)
        # # elif self.num == 800:
        #     target_LLA = [100.117, 13.618, 0]
        #     self.group_A(target_LLA,status=tank_status)

        if self.num > 2500:
            # 要是到最后几步了，就A到点里去好了。
            self.group_A(blue_deploy_LLA, status=( che_status |tank_status| ganraoche_status))    
            
        # 其他的，尝试搞一些博弈，比如侦测到对面从哪边过来，就相应地去防守那个方向。比如看见对面无人机过来了，就把干扰车开过去准备给它干扰了。原则上给它干扰了就能压制它传情报。由于开了干扰就全图可见，就还有分兵的说法。

        self.Gostep_abstract_state()
        return self.act  

    def step_blue_shishi3(self, status:dict):
        # 这个是重新做一个“根据敌方来的位置判断是冲着哪个房子来的，然后A过去附近看看”。
        fengedian = [] 
        fengedian.append([100.138,13.644,0])
        fengedian.append([100.158,13.649,0])

        # 由于是蓝方的，应该判断的方向是左中右了，看对面从哪边来，并安排相应的截击措施。
        if "direction_enemy" in self.blue_step_config:
            # 如果是这个，那就说明是已经定出来敌人在哪儿了
            enemy_direction = self.blue_step_config["direction_enemy"]
            flag_detected = True # False # 已经定出来了，后面不再更新了。
            # 这里其实等于true也无所谓，反正自己更新自己就是了，还可读性好一些。
        else:
            # 还没定出来，那就check一下。
            flag_detected, enemy_direction = self.check_enemy_direction2(self.detected_state2,fengedian,num_threshold=7)

        if (flag_detected == True or self.num > 800) and (not "flag_initialized" in self.blue_step_config)  :
            # 那就是开始行动,存一下全局变量。        
            self.blue_step_config["direction_enemy"] = enemy_direction
            self.blue_step_config["num_relative"] = 0 # 跟庙算的时候类似的，来一个相对的步数，方便。
            self.blue_step_config["flag_initialized"] = True # 得额外加一个标志位，不然就会在这里一直初始化，无法推进num_relative
            if enemy_direction == "left":
                # 敌方在右边，那么我方就去右边防御。
                LLA_list = [] 
                LLA_list.append([100.118, 13.6466, 0])  # 集结防御的点
                LLA_list.append([100.12, 13.6416, 0])  # 步兵下车前出的点
                num_list = [] 
                num_list.append(2)
                num_list.append(600)
                num_list.append(1500) # 开始机动反击的时间点。
            elif enemy_direction == "right":
                # 敌方在左边，那么我方就去左边防御
                LLA_list = [] 
                LLA_list.append([100.158, 13.6611, 0])  # 集结防御的点
                LLA_list.append([100.166, 13.6563, 0])  # 步兵下车前出的点
                num_list = [] 
                num_list.append(2)
                num_list.append(600)
                num_list.append(1500) # 开始机动反击的时间点。
            elif enemy_direction == "center":
                LLA_list = [] 
                LLA_list.append([100.137, 13.6479, 0])  # 集结防御的点
                LLA_list.append([100.137, 13.6424, 0])  # 步兵下车前出的点
                num_list = [] 
                num_list.append(2)
                num_list.append(600)
                num_list.append(1500) # 开始机动反击的时间点。
                pass
            self.blue_step_config["LLA_list"] = LLA_list
            self.blue_step_config["num_list"] = num_list
        # if self.num > 400 and not("direction_enemy" in self.blue_step_config):
        #     # 这个是大保底，如果到一定步数还没定下来，那就强行定一个，开始冲了。
        #     self.blue_step_config["direction_enemy"] = enemy_direction
        #     self.blue_step_config["num_relative"] = 0 # 跟庙算的时候类似的，来一个相对的步数，方便。

        # 然后后面就开始决策了，如果已经判断出了敌人方向，就往反方向突击，如果没有判断出敌人的方向，就去一个比较好的位置等一下。
        if not ("direction_enemy" in self.blue_step_config):
            # 那就是还没选定出击方向
            self.step_blue_shishi3_waiting(status)
        else:
            # 那就是已经选定出击方向
            self.step_blue_shishi3_moven(status)
        # 这句统一拿出来外面写了。
        self.Gostep_abstract_state()
        return self.act 
    
    def step_blue_shishi3_waiting(self, status:dict):
        # 蓝方的开局，也是先分兵走一段，派遣探测，然后A。
        self.act = [] 
        red_deploy_LLA = [100.15427471282, 13.60603147549, 0]
        blue_deploy_LLA = [100.12472961, 13.66152304, 0]
        # 先把兵种的分类做了
        bin_status = self.select_by_type("Infantry")
        bin1_status= dict()
        bin2_status = dict()
        bin_id_list = list(bin_status.keys())
        for i in range(len(bin_id_list)):
            if i <4:
                # 那就是机动步兵
                bin1_status[bin_id_list[i]] = bin_status[bin_id_list[i]]
            else:
                # 那就是驻防步兵
                bin2_status[bin_id_list[i]] = bin_status[bin_id_list[i]]
        tank_status = self.select_by_type("MainBattleTank")
        xiaoche_status = self.select_by_type("ArmoredTruck") 
        che_status = self.select_by_type("WheeledCmobatTruck")
        feiji_status = self.select_by_type("ShipboardCombat_plane")
        ganraoche_status = self.select_by_type("JammingTruck")
        xunfeidan_status = self.select_by_type("CruiseMissile")

        if self.num ==1:
            # 驻防步兵就开局直接进房子可也。
            self.set_hidden_and_alert(bin2_status)
            # 先知一飞开三矿
            xunfeidan_status1, xunfeidan_status2 = self.select_by_devide(xunfeidan_status)
            self.set_UAV_scout(feiji_status,red_deploy_LLA,R=4000)
            self.set_UAV_scout(xunfeidan_status1,[100.122, 13.622, 0],R=1500)
            self.set_UAV_scout(xunfeidan_status2,[100.164, 13.636, 0],R=1500)
            # # 干扰车冲一波看看成色。
            # self.set_move_and_jammer(ganraoche_status, red_deploy_LLA, model=-1)
        
        if self.num ==2:
            # 地面部队往前推进一些，适当分兵。# 硬编码虽然傻逼，但是反而好改。是所谓事异则备变。
            tank_status1, tank_status2 = self.select_by_devide(tank_status)
            # self.group_A([100.148,13.6555,0], status=(tank_status1 | ganraoche_status))    
            self.group_A([100.123,13.649,0], status=(tank_status1 | ganraoche_status))    
            self.group_A([100.143,13.646,0], status=tank_status2)    

            # 偷懒了，直接搞到中间点的位置去了.这样冲中路能顶住。
            self.group_A2([100.138, 13.6465, 0], che_status, bin1_status)

            # 干扰车应该是在动来动去的。恐怕比较好
            self.set_partrol_and_monitor(ganraoche_status, [100.133, 13.6545, 0])

    def step_blue_shishi3_moven(self, status:dict):
        # 别冲出去打，依托房子打，所以坦克那些别冲的太靠前。但是判明方向之后要重新部署，互相支援。
        self.act = [] 
        blue_deploy_LLA = [100.12472961, 13.66152304, 0]
        # 先把兵种的分类做了
        bin_status = self.select_by_type("Infantry")
        bin1_status= dict()
        bin2_status = dict()
        bin_id_list = list(bin_status.keys())
        for i in range(len(bin_id_list)):
            if i <4:
                # 那就是机动步兵
                bin1_status[bin_id_list[i]] = bin_status[bin_id_list[i]]
            else:
                # 那就是驻防步兵
                bin2_status[bin_id_list[i]] = bin_status[bin_id_list[i]]
        tank_status = self.select_by_type("MainBattleTank")
        xiaoche_status = self.select_by_type("ArmoredTruck") 
        che_status = self.select_by_type("WheeledCmobatTruck")
        feiji_status = self.select_by_type("ShipboardCombat_plane")
        ganraoche_status = self.select_by_type("JammingTruck")
        xunfeidan_status = self.select_by_type("CruiseMissile")

        # 然后从变量里面把进攻的路径点取出来。
        LLA_list = self.blue_step_config["LLA_list"]
        num_list = self.blue_step_config["num_list"]
        num_relative = self.blue_step_config["num_relative"]        

        if num_relative == num_list[0]:
            # 把坦克啊步兵啊什么的A到相关方向的房子后面。
            self.group_A(LLA_list[0], status=(tank_status))
            self.group_A2(LLA_list[0], che_status, bin1_status)
            self.set_partrol_and_monitor(ganraoche_status, LLA_list[0])
            # 把无人机和巡飞弹叫回来，在周围绕一下。
            self.set_UAV_scout(feiji_status, LLA_list[0],R=3000)
            self.set_UAV_scout(xunfeidan_status, LLA_list[0], R=2000)

        if num_relative == num_list[1]:
            # 步兵下车完成了，可以往前面走走。
            # 这个能形成一个相对好一些的阵形。
            self.group_A(LLA_list[1],status = (bin1_status | che_status))

        if num_relative >= num_list[2]:
            # 这里面就是“分点儿移动兵力出去进行反击”的说法了。1025：这逻辑有点问题，是A上去还是收缩防御效果更好，是一个需要聊一下的事情。
            tank_status1, tank_status2 = self.select_by_devide(tank_status)
            # 小车在步兵就位之后就完全可以派出去操作了
            jidong_status = che_status | tank_status1

            # 找到目标。
            n_fangxiang, LLA_ave = self.check_enemy_direction(self.detected_state2, blue_deploy_LLA )
            self.group_A(LLA_ave,status=jidong_status,vector_LLA=n_fangxiang)
            # self.group_A(LLA_ave,status=jidong_status)
            
        self.blue_step_config["num_relative"] = num_relative+1 

        pass

    def step_blue_shangxiache(self, status:dict):
        self.act= [] 
        # 这个是为了配合来哥好好测上下车的。
        location_list = [] 
        location_list.append([100.123,13.6682,0])
        location_list.append([100.114,13.6541,0])
        location_list.append([100.137,13.6589,0])
        # 先把兵种的分类做了
        bin_status = self.select_by_type("Infantry")
        bin1_status= dict()
        bin2_status = dict()
        bin_id_list = list(bin_status.keys())
        for i in range(len(bin_id_list)):
            if i <4:
                # 那就是机动步兵
                bin1_status[bin_id_list[i]] = bin_status[bin_id_list[i]]
            else:
                # 那就是驻防步兵
                bin2_status[bin_id_list[i]] = bin_status[bin_id_list[i]]
        tank_status = self.select_by_type("MainBattleTank")
        xiaoche_status = self.select_by_type("ArmoredTruck")
        che_status = self.select_by_type("WheeledCmobatTruck")
        feiji_status = self.select_by_type("ShipboardCombat_plane")
        ganraoche_status = self.select_by_type("JammingTruck")
        xunfeidan_status = self.select_by_type("CruiseMissile")

        if self.num % 1200 == 2:
            # 那就去第一个点  
            index = 0 
        elif self.num % 1200 == 402:
            # 那就去第二个点
            index = 1
        elif self.num % 1200 == 802:
            # 那就去第三个点
            index = 2 
        else:
            # 那就不重复发命令了
            index = -1 

        if index>=0:
            target_LLA =  location_list[index]
            self.group_A2(target_LLA, che_status, bin1_status)
        self.Gostep_abstract_state()
        return self.act 

    def step_LLM(self,status:dict):
        # 用于配合大模型的。说白了就是啥也不干，只走一波抽象状态。
        self.Gostep_abstract_state()
        return self.act         