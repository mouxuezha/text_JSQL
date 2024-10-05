import os.path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent.base_agent import BaseAgent
import copy


class GlobalAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.test_config =dict()
        self.num = 0

    def step(self,status):
        self.act = [] 
        self.status = status
        # print("unfinished yet")
        if self.player == "red":
            # 当前智能体是红方
            self.act = self.step_red_demo(status)
            # self.act = self.step_red_test_kaihuo(status)
            # self.act = self.step_red_test_move(status)
            # self.act = self.step_red_test_ganrao(status)
            # self.act = self.step_red_test_xunfeidan(status)
            # self.act = self.step_red_test_yueye(status)
            pass
        elif self.player == "blue":
            # 当前智能体是蓝方
            self.act = self.step_blue_demo(status)
            # self.act = self.step_blue_test_kaihuo(status)
            # self.act = self.step_blue_test_ganrao(status)
            # self.act = self.step_blue_test_building(status)
            pass 
        return self.act
    
    def reset(self):
        super().reset()
        # print("unfinished yet")
        pass

    def load_test_config(self,test_config):
        self.test_config = self.test_config | test_config
        pass
    
    def communication(self, local_agent_dict:dict):
        # 这个是用来实现全局和局部之间传输信息的。各参赛队伍可自行定制传输内容。
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

        if self.num >=0:
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
            # 专门用来看拦截的
            for equip in missile_truckID:
                my_LLA = self.get_LLA(equip,status=status)
                target_LLA=[100.137777,13.6442,0]
                self._Attack_Action(equip, target_LLA[0],target_LLA[1],target_LLA[2],MissleTruckMissileType[0])   
                                  
        return self.act

    def step_blue_demo(self, status:dict):
        self.act = [] 
        # 也是直接冲
        # target_LLA = [100.137777, 13.6442, 0 ]
        # ID_list = list(status.keys())
        WheeledCmobatTruck_ZB200 = self.select_by_type("WheeledCmobatTruck_ZB200")
        MainBattleTank_ZTZ200 = self.select_by_type("MainBattleTank_ZTZ200")
    
        WheeledCmobatTruck_ZB200ID = list(WheeledCmobatTruck_ZB200.keys())
        MainBattleTank_ZTZ200ID = list(MainBattleTank_ZTZ200.keys())

        if self.num == 2:
            # for ID_single in ID_list:
            #     # self._Change_State(ID_single,3)
            #     pass
            # 上下车演示：
            # 先上车
            for i in range(4):
                IFV_ID = "WheeledCmobatTruck_ZB200_" + str(i)
                infantry_ID = "Infantry" + str(i+2)
                self._On_Board_Action(IFV_ID, infantry_ID)  

        if self.num == 5:
            # 四个ZJ车载步兵冲向四个房子前
            target_LLA_step1_WheeledCmobatTruck_ZB200 = [(100.164, 13.656, 0),
                                                          (100.138, 13.6403, 0),
                                                          (100.117, 13.6414, 0),
                                                          (100.105, 13.6348, 0)]
            for i, target_single in enumerate(target_LLA_step1_WheeledCmobatTruck_ZB200):
                Id = WheeledCmobatTruck_ZB200ID[i]
                lon, lat, alt = target_single 
                self._Move_Action(Id, lon, lat, alt)
            # 坦克分两组向前冲
            target_LLA_step1_MainBattleTank_ZTZ200 = [(100.151, 13.6492, 0),
                                                      (100.151, 13.6492, 0),
                                                      (100.127, 13.641, 0),
                                                      (100.127, 13.641, 0)]
            for i, target_single in enumerate(target_LLA_step1_MainBattleTank_ZTZ200):
                Id = MainBattleTank_ZTZ200ID[i]
                lon, lat, alt = target_single 
                self._Move_Action(Id, lon, lat, alt)
            # 无人机随机巡逻
            patrol_area = [100.0923, 100.18707, 13.6024, 13.67248]
            self.random_patrol('ShipboardCombat_plane1', patrol_area, num_points=10)

            
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