# coding=UTF-8
from agent_guize.agent import Agent
import math
import numpy as np
import random
import collections
import time
import json

# 这个是服务于合代码而改出来的了

class RedAgent(Agent):
    def __init__(self):
        super(RedAgent, self).__init__()
        self.num = 0
        self.pos_lon = -0.4
        self.pos_lat = 0
        self.radius = 0.05
        self.theta = 0

        self.mb = ['', '', '']
        self.a = ['', '', '', '', '', '']
        self.whc = ['', '', '']
        self.m = ['', '']
        self.iftr = ['', '', '']
        self.hwz = ['', '', '']
        self.hd = ['']
        self.cop = ['', '', '', '', '']
        self.uavp = ['', '']

        self.status = []
        self.lure = set()  # 储存弹药耗尽的舰船ID，作为吸引敌方火力的诱饵

        self.mv_l = [False, False]

        self.len_act = 0

        self.deploy_modify_flag = False
        self.name_list = ["MainBattleTank_ZTZ100", "ArmoredTruck_ZTL100", "WheeledCmobatTruck_ZB100", "Howitzer_C100",
                          "missile_truck", "Infantry", "ShipboardCombat_plane"]
        self.last_order_num = 0

    def reset(self):
        self.num = 0

    def setTeam(self, player):
        setTeamAction = [{'Type': 'Set_team', 'Player': player, 'Name': 'YF_test'}]
        return setTeamAction

    def deploy(self, Ids):
        self.act = []
        Deployment_MainBattleTank_ZTZ100 = [[2.59, 39.72, 0, 30, 30], [2.59, 39.72, 0, 30, 30],
                                            [2.59, 39.72, 0, 30, 30],
                                            [2.59, 39.72, 0, 30, 30],
                                            ]
        Deployment_ArmoredTruck_ZTL100 = [[2.59, 39.72, 0], [2.59, 39.72, 0]]
        Deployment_WheeledCmobatTruck_ZB100 = [[2.59, 39.72, 0], [2.59, 39.72, 0]]
        Deployment_Howitzer_C100 = [[2.59, 39.72, 0, 40, 40]]
        Deployment_MissleTruck = [[2.6228, 41.6363, 0], [2.6238, 41.6373, 0], [2.6238, 41.6373, 0]]
        # 8个步兵班
        Deployment_Infantry = [[2.59, 39.72, 0], [2.59, 39.72, 0]]
        Deployment_ShipboardCombat_plane = [[2.59, 39.72, 800]]


        MissleTruckID = [id for id in Ids if "missile_truck" in id]  # DD营

        MainBattleTank_ZTZ100ID = [id for id in Ids if "MainBattleTank_ZTZ100" in id]  # 红方坦克营

        ArmoredTruck_ZTL100ID = [id for id in Ids if "ArmoredTruck_ZTL100" in id]  # 红方无人突击车

        Howitzer_C100ID = [id for id in Ids if "Howitzer_C100" in id]  # 自行迫榴炮

        WheeledCmobatTruck_ZB100ID = [id for id in Ids if "WheeledCmobatTruck_ZB100" in id]  # 轻型装甲车

        InfantryID = [id for id in Ids if "Infantry" in id]  # 步兵班

        ShipboardCombat_planeID = [id for id in Ids if "ShipboardCombat_plane" in id]  # 无人查打一体机

        MissleTruckID.sort()

        ArmoredTruck_ZTL100ID.sort()

        MainBattleTank_ZTZ100ID.sort()

        Howitzer_C100ID.sort()

        WheeledCmobatTruck_ZB100ID.sort()

        ShipboardCombat_planeID.sort()

        InfantryID.sort()

        # 传递名字列表
        self.mb = MainBattleTank_ZTZ100ID  # 主Zh坦克
        self.a = ArmoredTruck_ZTL100ID  # 装甲突击车
        self.whc = WheeledCmobatTruck_ZB100ID  # 轮式步战车
        self.hwz = Howitzer_C100ID  # 榴D炮
        self.m = MissleTruckID  # DDFS车
        self.iftr = InfantryID  # 步兵班
        self.sbc = ShipboardCombat_planeID  # 无人查打


        for i in range(len(MainBattleTank_ZTZ100ID)):
            self._ArmorCar_Deploy_Action(MainBattleTank_ZTZ100ID[i], Deployment_MainBattleTank_ZTZ100[i][0],
                                         Deployment_MainBattleTank_ZTZ100[i][1],
                                         Deployment_MainBattleTank_ZTZ100[i][2], Deployment_MainBattleTank_ZTZ100[i][3],
                                         Deployment_MainBattleTank_ZTZ100[i][4]
                                         )

        for i in range(len(ArmoredTruck_ZTL100ID)):
            self._Deploy_Action(ArmoredTruck_ZTL100ID[i], Deployment_ArmoredTruck_ZTL100[i][0],
                                Deployment_ArmoredTruck_ZTL100[i][1],
                                Deployment_ArmoredTruck_ZTL100[i][2])

        for i in range(len(WheeledCmobatTruck_ZB100ID)):
            self._Deploy_Action(WheeledCmobatTruck_ZB100ID[i], Deployment_WheeledCmobatTruck_ZB100[i][0],
                                Deployment_WheeledCmobatTruck_ZB100[i][1],
                                Deployment_WheeledCmobatTruck_ZB100[i][2])
        for i in range(len(Howitzer_C100ID)):
            self._ArmorCar_Deploy_Action(Howitzer_C100ID[i], Deployment_Howitzer_C100[i][0],
                                         Deployment_Howitzer_C100[i][1],
                                         Deployment_Howitzer_C100[i][2],
                                         Deployment_Howitzer_C100[i][3],
                                         Deployment_Howitzer_C100[i][4],
                                         )
        for i in range(len(MissleTruckID)):
            if MissleTruckID[i] != "":
                self._Deploy_Action(MissleTruckID[i], Deployment_MissleTruck[i][0],
                                    Deployment_MissleTruck[i][1],
                                    Deployment_MissleTruck[i][2]
                                    )
        for i in range(len(InfantryID)):
            self._Deploy_Action(InfantryID[i], Deployment_Infantry[i][0],
                                Deployment_Infantry[i][1],
                                Deployment_Infantry[i][2]
                                )
        # 增加部署无人机
        for i in range(len(ShipboardCombat_planeID)):
            self._Deploy_Action(ShipboardCombat_planeID[i], Deployment_ShipboardCombat_plane[i][0],
                                Deployment_ShipboardCombat_plane[i][1],
                                Deployment_ShipboardCombat_plane[i][2]
                                )
        return self.act

    def Weapon_estimate(self, status, ID, missileType):  # 判断D是否耗尽
        type = True
        for i in range(len(status[ID]["WeaponState"])):
            if status[ID]["WeaponState"][i]['WeaponType'] == missileType and \
                    status[ID]["WeaponState"][0]['WeaponNum'] == 0:
                type = False
        return type
    # 用装饰器
    # def distribute_group_command(self, groupid, command_type):
    #     if groupid not in self.groupmap.keys():
    #         return
    #     for unit_name in self.groupmap[groupid]:


    def step(self, status):
        # 各种战略战术就应该放在这里面，这里面原则上只调用那几个抽象命令，不直接调用接口

        nowtime = time.time()
        print("time per step: ", nowtime-self.time_)
        self.time_ = nowtime

        self.status = status
        self.num += 1
        self.act = []

        print("red agent")


        # 抽象命令的维护挪进来好了，减少相互耦合，没啥不好的讲道理。
        # self.Gostep_abstract_state(status=status)
        # 不对，不行，因为要输入获取地形的接口。所以要么改初始化，要么就这么用了。那先不慌动这个好了。1019

        if self.num == 1:
            self.Inint_abstract_state(self.status)  # 别的先就地隐蔽起来

        # self.step1(status)
        self.step1_1_1(status)
        # self.step1_2(status)
        # self.step1_3(status)
        # self.step1_4(status)
        # self.step2(status)

        # 兼容性，把Gostep放在这里面了
        self.Gostep_abstract_state()

        return self.act

    def step1(self, status):
        WheeledCombatTruck_ZB100ID = [id for id in status if "WheeledCmobatTruck_ZB100" in id]
        ArmoredTruck_ZTL100ID = [id for id in status if "ArmoredTruck_ZTL100" in id]
        MissleTruckID = [id for id in status if "missile_truck" in id]
        InfantryID = [id for id in status if "Infantry" in id and "Bullet_ZT" not in id]
        MainBattleTank_ZTZ100ID = [id for id in status if "MainBattleTank_ZTZ100" in id]
        Howitzer_C100ID = [id for id in status if "Howitzer_C100" in id]
        ShipboardCombat_planeID = [id for id in status if "ShipboardCombat_plane" in id]  # 无人查打一体机，添加
        # 这个是第一个成型的
        tank_status = self.select_by_type("MainBattleTank")
        xiaoche_status = self.select_by_type("Truck")
        jidong_status = {}
        jidong_status.update(tank_status)
        jidong_status.update(xiaoche_status)

        pao_status = self.select_by_type("Howitzer")
        bin_status = self.select_by_type("Infantry")
        daodan_status = self.select_by_type("missile_truck")
        fire_status = {}
        fire_status.update(pao_status)
        fire_status.update(daodan_status)

        # 约定一下，最外层只写self.num
        if self.num == 1:
            # 先上车
            for i in range(len(WheeledCombatTruck_ZB100ID)):
                self.set_none(WheeledCombatTruck_ZB100ID[i])  # 这个先关了一下
                self.set_none(InfantryID[i])  # 这个先关了一下
                self._On_Board_Action(WheeledCombatTruck_ZB100ID[i], InfantryID[i])
                # self._Off_Board_Action(WheeledCombatTruck_ZB100ID[i])
            self.last_order_num = self.num


        if (self.num >= 5 ) and (self.num <= 10):  # 每一条都应该想想，如果没执行成功会发生什么。得闭环别卡了
            # 到这应该算是上车完成了。保险起见再检测一下
            shishi_Infantry_status = self.select_by_type("Infantry")
            if (len(shishi_Infantry_status) == 0) or (self.num==10):
                # 那说明上车成功了。
                # 先A到附近去结阵。
                target_LLA = [2.71 - 0.02, 39.76 - 0.02, 0]
                self.group_A(target_LLA, status=self.status)
                self.last_order_num = self.num

        # 到这里就已经是整体的A过去了，而且隐蔽起来了。下个车。
        if (self.num >= 100 and self.num <= 105):
            for i in range(len(WheeledCombatTruck_ZB100ID)):
                self.set_none(WheeledCombatTruck_ZB100ID[i])  # 这个先关了一下
                self._Off_Board_Action(WheeledCombatTruck_ZB100ID[i])
            self.last_order_num = self.num

        target_LLA = [2.71-0.01, 39.76-0.01, 0]
        if (self.num >= 250 and self.num <= 350):  # 还是别偷懒
            if (self.check_all_finished(status=jidong_status) or self.num == 350):
                # 那就算是A过去了，那就下一个点
                self.group_A(target_LLA,status=jidong_status)
                last_order_num = self.num

        target_LLA = [2.71, 39.76, 0]  # 分两段，A过去。
        if (self.num >= 350 and self.num <= 450):  # 还是别偷懒
            if (self.check_all_finished(status=jidong_status) or self.num == 450):
                # 那就算是A过去了，那就下一个点
                self.group_A(target_LLA,status=jidong_status)
                # 防御力量不动，但是开火，嘎嘎乱杀。
                self.set_open_fire(fire_status)
                last_order_num = self.num

        if self.num >450:
            # 这个分支处理如果到了之后探测到敌方，要怎么搞。

            # 先探测一下，如果有合适的就直接结阵A过去
            self.detected_state = self.get_detect_info(self.status)
            if len(self.detected_state) > 2 :
                # 那就是探测到东西了，咬它！
                if len(jidong_status) > 0 :
                    attacker_ID = list(jidong_status.keys())[0]
                    target_ID_local, target_LLA_local, target_distance_local \
                        = self.range_estimate2(attacker_ID, self.detected_state)
                    if not("ShipboardCombat" in target_ID_local):
                        # 只出动机动力量.
                        self.group_A(target_LLA_local, status=jidong_status)

                pao_list = list(pao_status.keys())
                if len(pao_list)>0:
                    # 说明炮还在
                    self.set_follow_and_defend(bin_status, pao_list[0])
                else:
                    # 说明炮被打烂了。
                    self.group_A(target_LLA, status=bin_status)
                last_order_num = self.num
            else:
                # 那就是没探测到东西，那就A回去，不要在外面逗留
                target_LLA = [2.71, 39.76, 0]
                self.group_A(target_LLA,status=jidong_status)
                last_order_num = self.num

        return self.act

    def step1_1(self, status):
        WheeledCombatTruck_ZB100ID = [id for id in status if "WheeledCmobatTruck_ZB100" in id]
        ArmoredTruck_ZTL100ID = [id for id in status if "ArmoredTruck_ZTL100" in id]
        MissleTruckID = [id for id in status if "missile_truck" in id]
        InfantryID = [id for id in status if "Infantry" in id and "Bullet_ZT" not in id]
        MainBattleTank_ZTZ100ID = [id for id in status if "MainBattleTank_ZTZ100" in id]
        Howitzer_C100ID = [id for id in status if "Howitzer_C100" in id]
        ShipboardCombat_planeID = [id for id in status if "ShipboardCombat_plane" in id]  # 无人查打一体机，添加
        tank_status = self.select_by_type("MainBattleTank")
        xiaoche_status = self.select_by_type("Truck")
        jidong_status = {}
        jidong_status.update(tank_status)
        jidong_status.update(xiaoche_status)

        pao_status = self.select_by_type("Howitzer")
        bin_status = self.select_by_type("Infantry")
        daodan_status = self.select_by_type("missile_truck")
        fire_status = {}
        fire_status.update(pao_status)
        fire_status.update(daodan_status)

        # 约定一下，最外层只写self.num
        if self.num == 1:
            # 先上车
            self.Inint_abstract_state(self.status)  # 别的先就地隐蔽起来

            for i in range(len(WheeledCombatTruck_ZB100ID)):
                self.set_none(WheeledCombatTruck_ZB100ID[i])  # 这个先关了一下
                self.set_none(InfantryID[i])  # 这个先关了一下
                self._On_Board_Action(WheeledCombatTruck_ZB100ID[i], InfantryID[i])
                # self._Off_Board_Action(WheeledCombatTruck_ZB100ID[i])
            self.last_order_num = self.num


        if (self.num >= 5 ) and (self.num <= 10):  # 每一条都应该想想，如果没执行成功会发生什么。得闭环别卡了
            # 到这应该算是上车完成了。保险起见再检测一下
            shishi_Infantry_status = self.select_by_type("Infantry")
            if (len(shishi_Infantry_status) == 0) or (self.num==10):
                # 那说明上车成功了。
                # 先A到附近去结阵。
                target_LLA = [2.68, 39.74, 0]
                # target_LLA = [2.71 - 0.02, 39.76 - 0.02, 0]
                self.group_A(target_LLA, status=self.status)
                self.last_order_num = self.num

        # 到这里就已经是整体的A过去了，而且隐蔽起来了。下个车。
        if (self.num >= 300 and self.num <= 305):
            for i in range(len(WheeledCombatTruck_ZB100ID)):
                self.set_none(WheeledCombatTruck_ZB100ID[i])  # 这个先关了一下
                self._Off_Board_Action(WheeledCombatTruck_ZB100ID[i])
            self.last_order_num = self.num

        target_LLA = [2.71-0.001, 39.76-0.001, 0]
        if (self.num >= 305 and self.num <= 405):  # 还是别偷懒
            if (self.check_all_finished(status=jidong_status) or self.num == 405):
                # 那就算是A过去了，那就下一个点
                self.group_A(target_LLA, status=jidong_status)
                last_order_num = self.num

        target_LLA = [2.71, 39.76, 0]  # 分两段，A过去。
        if (self.num >= 405 and self.num <= 505):  # 还是别偷懒
            if (self.check_all_finished(status=jidong_status) or self.num == 505):
                # 那就算是A过去了，那就下一个点
                self.group_A(target_LLA, status=jidong_status)
                # 防御力量不动，但是开火，嘎嘎乱杀。
                self.set_open_fire(fire_status)
                last_order_num = self.num

        if self.num >505:
            # 这个分支处理如果到了之后探测到敌方，要怎么搞。

            # 先探测一下，如果有合适的就直接结阵A过去
            self.detected_state = self.get_detect_info(self.status)
            if len(self.detected_state) > 2 :
                # 那就是探测到东西了，咬它！
                if len(jidong_status) > 0 :
                    attacker_ID = list(jidong_status.keys())[0]
                    target_ID_local, target_LLA_local, target_distance_local \
                        = self.range_estimate2(attacker_ID, self.detected_state)
                    if not("ShipboardCombat" in target_ID_local):
                        # 只出动机动力量.
                        self.group_A(target_LLA_local, status=jidong_status)

                pao_list = list(pao_status.keys())

                if len(pao_list)>0:
                    # 说明炮还在
                    self.set_follow_and_defend(bin_status, pao_list[0])
                else:
                    # 说明炮被打烂了。
                    self.group_A(target_LLA, status=bin_status)
                last_order_num = self.num
            else:
                # 那就是没探测到东西，那就A回去，不要在外面逗留
                target_LLA = [2.71, 39.76, 0]
                self.group_A(target_LLA, status=jidong_status)
                last_order_num = self.num

        return self.act

    def step1_1_1(self, status):
        # 这版再改改打太初的，看能不能多打出几分净胜分来。以及改改占点的逻辑
        # 这个是用来针对某个强队的蓝方的，完全放弃占点，跟他A一波正面。
        tank_status = self.select_by_type("MainBattleTank")
        xiaoche_status = self.select_by_type("ArmoredTruck")
        che_status = self.select_by_type("WheeledCmobatTruck")
        feiji_status = self.select_by_type("ShipboardCombat_plane")
        jidong_status = {}
        jidong_status.update(tank_status)
        jidong_status.update(xiaoche_status)

        pao_status = self.select_by_type("Howitzer")
        bin_status = self.select_by_type("Infantry")
        daodan_status = self.select_by_type("missile_truck")
        fire_status = {}
        fire_status.update(pao_status)
        fire_status.update(daodan_status)

        # 约定一下，最外层只写self.num
        # target_LLA = [2.69, 39.75, 0]
        target_LLA = [2.68, 39.74, 0]
        pao_LLA = [2.67, 39.75, 0]
        if self.num == 1:
            # 先上车
            self.group_A(target_LLA, status=self.status)
            self.group_A2(target_LLA, che_status, bin_status) # 原则上会盖了的，看行不行
            # self.group_A([2.71, 39.76, 0], status=xiaoche_status)
            self.group_A(pao_LLA, status=pao_status)
            self.last_order_num = self.num
            # self.set_none(daodan_status)

        # if self.num == 10:
        #     shishi = len(bin_status)
        #     print(shishi)

        target_LLA = [2.71-0.001, 39.76-0.001, 0]
        if (self.num >= 405 and self.num <= 505):  # 还是别偷懒
            if (self.check_all_finished(status=jidong_status) or self.num == 405):
                # 那就算是A过去了，那就下一个点
                jidong_status.update(che_status)
                jidong_status.update(bin_status)
                jidong_status.update(daodan_status)
                self.group_A(target_LLA, status=jidong_status)

                last_order_num = self.num

        target_LLA = [2.71, 39.76, 0]  # 分两段，A过去。
        if (self.num >= 505 and self.num <= 605):  # 还是别偷懒
            if (self.check_all_finished(status=jidong_status) or self.num == 505):
                # 那就算是A过去了，那就下一个点
                jidong_status.update(che_status)
                jidong_status.update(bin_status)
                self.group_A(target_LLA, status=jidong_status)
                # 防御力量不动，但是开火，嘎嘎乱杀。
                self.set_open_fire(fire_status)
                last_order_num = self.num

        if self.num >605 and self.num<2000:
            # 这个分支处理如果到了之后探测到敌方，要怎么搞。

            # 先探测一下，如果有合适的就直接结阵A过去
            self.detected_state = self.get_detect_info(self.status)
            if len(self.detected_state) > 2 :
                # 那就是探测到东西了，咬它！
                if len(jidong_status) > 0 :
                    attacker_ID = list(jidong_status.keys())[0]
                    target_ID_local, target_LLA_local, target_distance_local \
                        = self.range_estimate2(attacker_ID, self.detected_state)
                    if not("ShipboardCombat" in target_ID_local):
                        # 只出动机动力量.
                        self.group_A(target_LLA_local, status=jidong_status)

                pao_list = list(pao_status.keys())

                if len(pao_list)>0:
                    # 说明炮还在
                    self.set_follow_and_defend(bin_status, pao_list[0])
                else:
                    # 说明炮被打烂了。
                    self.group_A(target_LLA, status=bin_status)
                last_order_num = self.num
            else:
                # 那就是没探测到东西，那就A回去，不要在外面逗留
                target_LLA = [2.71, 39.76, 70]
                self.group_A(target_LLA, status=jidong_status)
                last_order_num = self.num
        elif self.num == 2000:
            target_LLA = [2.71, 39.76, 70]
            self.F2A(target_LLA)
        elif self.num == 2500:
            target_LLA = [2.71, 39.76, 70]
            self.F2A(target_LLA)
        if ((self.num % 20 ==10) or (self.flag_zhandian == False)) and (self.num > 1500):
            self.group_zhandian(self.status, target_LLA = [2.71, 39.76, 90])
        return self.act

    def step1_2(self, status):
        # WheeledCombatTruck_ZB100ID = [id for id in status if "WheeledCmobatTruck_ZB100" in id]
        # ArmoredTruck_ZTL100ID = [id for id in status if "ArmoredTruck_ZTL100" in id]
        # MissleTruckID = [id for id in status if "missile_truck" in id]
        # InfantryID = [id for id in status if "Infantry" in id and "Bullet_ZT" not in id]
        # MainBattleTank_ZTZ100ID = [id for id in status if "MainBattleTank_ZTZ100" in id]
        # Howitzer_C100ID = [id for id in status if "Howitzer_C100" in id]
        # ShipboardCombat_planeID = [id for id in status if "ShipboardCombat_plane" in id]  # 无人查打一体机，添加
        tank_status = self.select_by_type("MainBattleTank")
        xiaoche_status = self.select_by_type("ArmoredTruck")
        che_status = self.select_by_type("WheeledCmobatTruck")
        feiji_status = self.select_by_type("ShipboardCombat_plane")
        jidong_status = {}
        jidong_status.update(tank_status)
        jidong_status.update(xiaoche_status)
        jidong_status.update(feiji_status)

        pao_status = self.select_by_type("Howitzer")
        bin_status = self.select_by_type("Infantry")
        daodan_status = self.select_by_type("missile_truck")
        fire_status = {}
        fire_status.update(pao_status)
        fire_status.update(daodan_status)

        # 约定一下，最外层只写self.num，要优雅
        # target_LLA = [2.65, 39.75, 0] # 先别冲太近，对齐一下。这个位置是海边平地，比较好机动。500
        # target_LLA = [2.62, 39.74, 0]  # 先别冲太近，250


        target_LLA = [2.68984, 39.7, 186]  # 再走一段
        # target_LLA = [2.67967, 39.7981, 43.24]
        if self.num == 1:
            # 先上车
            jidong_status = {}
            # jidong_status.update(che_status)
            # jidong_status.update(bin_status)
            jidong_status.update(tank_status)
            jidong_status.update(xiaoche_status)
            jidong_status.update(feiji_status)
            self.group_A2(target_LLA, che_status, bin_status)
            self.group_A(target_LLA, status=jidong_status)
            # self.group_A(target_LLA,status=pao_status)
            # 跟随不保熟
            # tank_ID_list = list(tank_status.keys())
            # self.set_follow_and_defend(xiaoche_status, tank_ID_list[0])
            # 直接开炮，没什么好说的
            self.set_open_fire(daodan_status, target_LLA=[2.68984, 39.7, 186])
            # self.set_open_fire(pao_status, target_LLA=[2.68984, 39.7, 186])
            self.set_none(pao_status)
            self._Move_Action("Howitzer_C100_0", 2.6344, 39.7624, 47.571 )
            self.last_order_num = self.num

        if self.num == 600:
            # 认为炮已经到位了，隐蔽好了，直接开火
            # 后面点再开火
            self.set_open_fire(daodan_status, target_LLA=[2.71, 39.76, 50])
            self.set_open_fire(pao_status, target_LLA=[2.71, 39.76, 50])


        # if self.num == 300 :
        # if (len(bin_status)==2 and self.num>200 and self.last_order_num<200):
        #     # A过去了，而且应该下好车了，整理一下阵形。
        #     status_ordered = {}
        #     status_ordered.update(bin_status)
        #     status_ordered.update(che_status) # 兵和小车放在外层
        #     status_ordered.update(xiaoche_status)
        #     status_ordered.update(tank_status)
        #     self.group_D(status=status_ordered)
        #     self.last_order_num = self.num

        # target_LLA = [2.65, 39.75, 300]  # 再走一段
        # if self.num == 280:
        #     self.group_A2(target_LLA, che_status, bin_status)
        #     self.group_A(target_LLA, status=jidong_status)
        #     self.last_order_num = self.num
        # if self.num == 500:
        #     # A过去了，而且应该下好车了，整理一下阵形。
        #     status_ordered = {}
        #     status_ordered.update(bin_status)
        #     status_ordered.update(che_status) # 兵和小车放在外层
        #     status_ordered.update(xiaoche_status)
        #     status_ordered.update(tank_status)
        #     self.group_D(status=status_ordered)

        # target_LLA = [2.68, 39.755, 30]  # 再走一段
        target_LLA = [2.71, 39.76, 70]
        if self.num == 520:
            # jidong_status.update(che_status)
            # jidong_status.update(bin_status)
            self.group_A2(target_LLA, che_status, bin_status)
            self.group_A(target_LLA, status=jidong_status)
            self.last_order_num = self.num
        if self.num == 540:
            # A过去了，而且应该下好车了，整理一下阵形。
            status_ordered = {}
            status_ordered.update(bin_status)
            status_ordered.update(che_status) # 兵和小车放在外层
            status_ordered.update(xiaoche_status)
            status_ordered.update(tank_status)
            self.group_D(status=status_ordered)

        target_LLA = [2.71, 39.76, 70]
        if self.num == 600:
            status_ordered = {}
            status_ordered.update(bin_status)
            status_ordered.update(che_status)  # 兵和小车放在外层
            status_ordered.update(xiaoche_status)
            status_ordered.update(tank_status)
            self.group_A(target_LLA, status=status_ordered)

        # 然后是处理打起来之后的情况了。
        jidong_status.update(bin_status)
        if (self.num >700) and (self.num <=2000):
            # 这个分支处理如果到了之后探测到敌方，要怎么搞。

            jidong_status.update(che_status)
            jidong_status.update(bin_status)
            # 先探测一下，如果有合适的就直接结阵A过去
            self.detected_state = self.get_detect_info(self.status)
            if len(self.detected_state) > 2 :
                # 那就是探测到东西了，咬它！
                if len(jidong_status) > 0 :
                    attacker_ID = list(jidong_status.keys())[0]
                    target_ID_local, target_LLA_local, target_distance_local \
                        = self.range_estimate2(attacker_ID, self.detected_state)
                    if not("ShipboardCombat" in target_ID_local):
                        # 只出动机动力量.
                        self.group_A(target_LLA_local, status=jidong_status)

                pao_list = list(pao_status.keys())

                # if len(pao_list)>0:
                #     # 说明炮还在
                #     self.set_follow_and_defend(bin_status, pao_list[0])
                # else:
                #     # 说明炮被打烂了。
                #     self.group_A(target_LLA, status=bin_status)
                last_order_num = self.num
            else:
                # 那就是没探测到东西，那就A回去，不要在外面逗留
                target_LLA = [2.71, 39.76, 70]
                self.group_A(target_LLA, status=jidong_status)
                last_order_num = self.num

        elif self.num == 2000:
            # A过去
            jidong_status.update(che_status)
            jidong_status.update(bin_status)
            target_LLA = [2.71, 39.76, 70]
            self.group_A(target_LLA, status=jidong_status)
            # 这里就应该检测一下下车。
        elif self.num == 2500:
            # A过去
            jidong_status.update(che_status)
            jidong_status.update(bin_status)
            target_LLA = [2.71, 39.76, 70]
            self.group_A(target_LLA, status=jidong_status)

        return self.act

    def step1_3(self, status):
        # 这个经过测试，能够打过LGD、908、深度遗忘，最后都是有点的，鉴定为女子。
        tank_status = self.select_by_type("MainBattleTank")
        xiaoche_status = self.select_by_type("ArmoredTruck")
        che_status = self.select_by_type("WheeledCmobatTruck")
        feiji_status = self.select_by_type("ShipboardCombat_plane")
        jidong_status = {}
        jidong_status.update(tank_status)
        jidong_status.update(xiaoche_status)
        jidong_status.update(feiji_status)

        pao_status = self.select_by_type("Howitzer")
        bin_status = self.select_by_type("Infantry")
        daodan_status = self.select_by_type("missile_truck")
        fire_status = {}
        fire_status.update(pao_status)
        fire_status.update(daodan_status)

        # 约定一下，最外层只写self.num，要优雅
        # target_LLA = [2.65, 39.75, 0] # 先别冲太近，对齐一下。这个位置是海边平地，比较好机动。500
        # target_LLA = [2.62, 39.74, 0]  # 先别冲太近，250


        target_LLA = [2.68984, 39.7, 186]  # 再走一段
        # target_LLA = [2.67967, 39.7981, 43.24]
        target_LLA = [2.70, 39.76, 186]
        if self.num == 2:
            # 先上车
            jidong_status = {}
            # jidong_status.update(che_status)
            # jidong_status.update(bin_status)
            jidong_status.update(tank_status)
            jidong_status.update(xiaoche_status)
            jidong_status.update(feiji_status)
            self.group_A2(target_LLA, che_status, bin_status)
            self.group_A(target_LLA, status=jidong_status)

            # self.set_open_fire(daodan_status, target_LLA=[2.68984, 39.7, 186])
            self.set_none(daodan_status)  # 先蹲一会儿

            # self._Move_Action("Howitzer_C100_0", 2.647, 39.75, 47.571)
            self.last_order_num = self.num
        if self.num<3:
            self.set_none(pao_status)
            # self._Move_Action("Howitzer_C100_0", 2.6344, 39.7624, 47.571 )
            self.group_A([2.66, 39.76, 419], status=pao_status)

        if self.num == 600:
            # 认为炮已经到位了，隐蔽好了，直接开火
            # 后面点再开火
            self.set_open_fire(pao_status, target_LLA=[2.71, 39.76, 50])
        if self.num == 700:
            self.set_open_fire(daodan_status, target_LLA=[2.71, 39.76, 50])

        # 然后是处理打起来之后的情况了。
        jidong_status.update(bin_status)

        if (self.num >700) and (self.num <=2000):
            # 这个分支处理如果到了之后探测到敌方，要怎么搞。
            jidong_status.update(che_status)
            jidong_status.update(bin_status)
            # 先探测一下，如果有合适的就直接结阵A过去
            self.detected_state = self.get_detect_info(self.status)
            ave_LLA = self.get_LLA_ave(jidong_status)
            jvli = self.distance(target_LLA[0], target_LLA[1], target_LLA[2],
                                 ave_LLA[0], ave_LLA[1], ave_LLA[2])

            if (len(self.detected_state) > 2) and (jvli<1000) :
                # 那就是探测到东西了，咬它！
                if len(jidong_status) > 0 :
                    attacker_ID = list(jidong_status.keys())[0]
                    target_ID_local, target_LLA_local, target_distance_local \
                        = self.range_estimate2(attacker_ID, self.detected_state)
                    if not("ShipboardCombat" in target_ID_local):
                        # 只出动机动力量.
                        self.group_A(target_LLA_local, status=jidong_status)

                # pao_list = list(pao_status.keys())

                # if len(pao_list)>0:
                #     # 说明炮还在
                #     self.set_follow_and_defend(bin_status, pao_list[0])
                # else:
                #     # 说明炮被打烂了。
                #     self.group_A(target_LLA, status=bin_status)
                last_order_num = self.num
            else:
                # 那就是没探测到东西，那就A回去，不要在外面逗留
                if self.num % 114 == 0:
                    target_LLA = [2.71, 39.76, 70]
                    self.group_A(target_LLA, status=jidong_status)
                last_order_num = self.num

        elif self.num == 2000:
            # A过去
            jidong_status.update(che_status)
            jidong_status.update(bin_status)
            target_LLA = [2.71, 39.76, 70]
            self.group_A(target_LLA, status=jidong_status)
            # 这里就应该检测一下下车。
        elif self.num == 2500:
            # A过去
            target_LLA = [2.71, 39.76, 70]
            self.F2A(target_LLA)
        return self.act

    def step1_4(self, status):
        # 这个是用来针对某个强队的蓝方的，完全放弃占点，跟他A一波正面。
        tank_status = self.select_by_type("MainBattleTank")
        xiaoche_status = self.select_by_type("ArmoredTruck")
        che_status = self.select_by_type("WheeledCmobatTruck")
        feiji_status = self.select_by_type("ShipboardCombat_plane")
        jidong_status = {}
        jidong_status.update(tank_status)
        jidong_status.update(xiaoche_status)

        pao_status = self.select_by_type("Howitzer")
        bin_status = self.select_by_type("Infantry")
        daodan_status = self.select_by_type("missile_truck")
        fire_status = {}
        fire_status.update(pao_status)
        fire_status.update(daodan_status)

        xiache_LLA = [2.648, 39.716, 691.681]
        target_LLA = [2.71, 39.76, 70]
        if self.num == 1:
            # 先上车
            jidong_status = {}
            # jidong_status.update(che_status)
            # jidong_status.update(bin_status)
            jidong_status.update(tank_status)
            jidong_status.update(xiaoche_status)
            jidong_status.update(feiji_status)
            self.group_A2(xiache_LLA, che_status, bin_status)
            self.group_A(xiache_LLA, status=jidong_status)

            # self.set_open_fire(daodan_status, target_LLA=[2.68984, 39.7, 186])
            self.set_none(daodan_status)  # 先蹲一会儿

            # self._Move_Action("Howitzer_C100_0", 2.647, 39.75, 47.571)
            self.last_order_num = self.num
        elif self.num == 2:
            self.set_none(pao_status)
            # self._Move_Action("Howitzer_C100_0", 2.6344, 39.7624, 47.571 )
            self.group_A([2.64, 39.72, 910], status=pao_status)

        # target_LLA = [2.68984, 39.70, 130]
        target_LLA = [2.72, 39.73, 130]
        if (self.num >= 300) and (self.num<=600):
            # 第一轮都到位了，该下的车也下了，跟他结阵A一波正面，行不行就这波了。
            jidong_status = {}
            jidong_status.update(xiaoche_status)
            jidong_status.update(che_status)
            jidong_status.update(bin_status)
            jidong_status.update(tank_status)
            jidong_status.update(feiji_status)

            self.group_A_gai(xiache_LLA, jidong_status)
            if self.num == 600:
                # 架构没整好，导致要这么写。罢了，复盘的时候再慢慢说。
                self.group_A_gai_reset()

        if self.num > 600:
            jidong_status = {}
            jidong_status.update(xiaoche_status)
            jidong_status.update(che_status)
            jidong_status.update(bin_status)
            jidong_status.update(tank_status)
            jidong_status.update(feiji_status)
            self.group_A(target_LLA, status=jidong_status)

        # 然后就新常态了。防守某个点
        target_LLA = [2.71, 39.76, 70]
        if (self.num > 1000) and (self.num <= 2500):
            # 先探测一下，如果有合适的就直接结阵A过去
            # 重新排序阵法，A上去。
            jidong_status = {}
            jidong_status.update(che_status)
            jidong_status.update(bin_status)
            jidong_status.update(tank_status)
            jidong_status.update(feiji_status)
            self.detected_state = self.get_detect_info(self.status)
            if len(self.detected_state) > 3: # and len(self.detected_state) < 10 :
                # 那就是探测到东西了，咬它！
                # 先探测一下，如果有合适的就直接结阵A过去
                self.detected_state = self.get_detect_info(self.status)
                attacker_ID = list(jidong_status.keys())[-1]
                target_ID_local, target_LLA_local, target_distance_local \
                    = self.range_estimate_gai(attacker_ID, self.detected_state)
                ave_LLA = self.get_LLA_ave(jidong_status)
                jvli = self.distance(target_LLA[0], target_LLA[1], target_LLA[2],
                                     ave_LLA[0], ave_LLA[1], ave_LLA[2])

                if (len(target_ID_local) > 0) and (jvli<500) :
                    # 那就是探测到东西了，咬它！
                    # 确切地说，如果探测到的东西值得杀过去，那就杀过去，不然就不杀过去了。
                    if len(target_ID_local)>0:
                        self.group_A(target_LLA_local, status=jidong_status)
                        self.group_A_gai(target_LLA_local, status=tank_status)

                        self.group_A(target_LLA, status=daodan_status)
                    self.last_order_num = self.num
                elif jvli>1000: # 那就是鉴定为危险？
                    self.group_A(target_LLA, status=jidong_status)
                    pass
                else:
                    # 那就是没探测到东西，那就A回去，不要在外面逗留
                    if self.num % 114 == 0:
                        self.group_A(target_LLA, status = jidong_status)
                        self.F2A(target_LLA, status = che_status)
                        self.group_A(target_LLA, status=daodan_status) # 这个跑路
                        self.last_order_num = self.num
        elif self.num == 2500:
            # A过去
            target_LLA = [2.71, 39.76, 70]
            self.F2A(target_LLA)
        elif self.num == 2900:
            # A过去
            target_LLA = [2.71, 39.76, 70]
            self.F2A(target_LLA)

    def step2(self, status):
        # 这个是用来测试的
        tank_status = self.select_by_type("MainBattleTank")
        xiaoche_status = self.select_by_type("ArmoredTruck")
        che_status = self.select_by_type("WheeledCmobatTruck")
        jidong_status = {}
        jidong_status.update(tank_status)
        jidong_status.update(xiaoche_status)

        pao_status = self.select_by_type("Howitzer")
        bin_status = self.select_by_type("Infantry")
        daodan_status = self.select_by_type("missile_truck")
        fire_status = {}
        fire_status.update(pao_status)
        fire_status.update(daodan_status)

        # target_LLA = [2.61, 39.70, 100]
        # if self.num==1:
        #     self.set_partrol_and_monitor(jidong_status, target_LLA)
        # target_LLA = [2.75, 39.78, 0]
        # # self.group_A(target_LLA, status=bin_status)
        self.F2S()
        pass

    def checkNumMissle(self, state, shipID, missletype='ShipToShip_missile'):
        if missletype in state[shipID]['WeaponState'][0]['WeaponID']:
            return state[shipID]['WeaponState'][0]['WeaponNum']
        else:
            return state[shipID]['WeaponState'][1]['WeaponNum']


    def deploy_modify_set(self,my_unit_type, my_weapon_type, target_unit_type, location = [2.68, 39.70,0], index = 0 ):
        # 修改相应的东西的位置
        self.modify_unit_type = my_unit_type
        self.modify_location = location
        self.modify_index = index
        self.modify_weapon_type = my_weapon_type
        self.target_unit_type = target_unit_type

        self.deploy_modify_flag = True  # En Taro XXH!
        return 0

    def deploy_modify_location(self, *args):

        if self.deploy_modify_flag:
            # modify enabled
            print('red_agent: deploy_modify enabled')
            for i in range(len(self.name_list)):
                if self.name_list[i] in self.modify_unit_type:
                    for j in range(3):
                        args[i][0][j] = self.modify_location[j]
        return args
        # return Deployment_MainBattleTank_ZTZ100,Deployment_ArmoredTruck_ZTL100,Deployment_WheeledCombatTruck,\
        # Deployment_Howitzer_C100,Deployment_MissleTruck,Deployment_Infantry, Deployment_ShipboardCombat_plane

    def deploy_modify_attack(self):
        # 组装一个攻击命令，用来操作。
        ID_attacker = self.__get_attacker()
        # 攻击坐标就硬编码了先，应该跟目标坐标相匹配，才打得了。
        # self._Attack_Action(ID_attacker, 2.6801, 39.701, 390, self.modify_weapon_type)
        self._Attack_Action(ID_attacker, self.modify_location[0] + 0.0001, self.modify_location[1] + 0.001, 0, self.modify_weapon_type)
        return 0

    def deoply_modify_getstate(self, state='stay'):
        # enum
        # VehicleMoveState
        # {
        #     move, // 移动
        # stay, // 停止
        # hidden // 掩蔽
        # };
        self.modify_state = state

    def __get_attacker(self):
        if (self.modify_unit_type == self.name_list[5]) or (self.modify_unit_type == self.name_list[4]):
            ID_attacker = self.modify_unit_type + str(self.modify_index)  # 导弹车和步兵的编号方式不一样
        else:
            ID_attacker = self.modify_unit_type + '_' + str(self.modify_index)
        return ID_attacker

    def deploy_modify_setstate(self, time_step):
        # 组装一个move指令，每一帧都变化，然后让它围着中心点转。
        dL = 0.0002
        ID_attacker = self.__get_attacker()

        if self.modify_state == 'move':
            print("XXHtest: attacker move")
            # 按理说这样就可以持续绕圈圈。
            # 据力炜说，不要也行，可以直接设定成move
            if(time_step%4==0):
                self._Move_Action(ID_attacker, self.modify_location[0] - dL, self.modify_location[1] - dL, 0)
            elif(time_step%4==1):
                self._Move_Action(ID_attacker, self.modify_location[0] - dL, self.modify_location[1] + dL, 0)
            elif(time_step%4==2):
                self._Move_Action(ID_attacker, self.modify_location[0] + dL, self.modify_location[1] - dL, 0)
            elif(time_step%4==2):
                self._Move_Action(ID_attacker, self.modify_location[0] + dL, self.modify_location[1] + dL, 0)
        elif self.modify_state == 'stay':
            print("XXHtest: attacker stay")
            self._Change_State(ID_attacker, self.modify_state)
        elif self.modify_state == 'hidden':
            print("XXHtest: attacker hidden")
            self._Change_State(ID_attacker, self.modify_state)

        return 0