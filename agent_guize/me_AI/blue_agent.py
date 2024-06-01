# coding=UTF-8
from agent_guize.agent import Agent
import math
import numpy as np
import random
import collections
import json


class BlueAgent(Agent):
    def __init__(self):
        super(BlueAgent, self).__init__()
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
        self.name_list = ["MainBattleTank_ZTZ200", "missile_truck","WheeledCmobatTruck_ZB200","Infantry",  "ArmoredTruck_ZTL100",  "Howitzer_C100",
                           "HeavyDestroyer_Ship"]
    def reset(self):
        self.num = 0

    def setTeam(self, player):
        setTeamAction = [{'Type': 'Set_team', 'Player': player, 'Name': 'YF_test'}]
        return setTeamAction

    # def deploy(self):
    #     self.act = []
    #     Deployment_MainBattleTank_ZTZ200 = self.load_xlsx_deploy("Deployment_MainBattleTank_ZTZ200")
    #     Deployment_WheeledCombatTruck_ZB200 = self.load_xlsx_deploy("Deployment_WheeledCombatTruck_ZB200")
    #     Deployment_MissleTruck = self.load_xlsx_deploy("Deployment_MissleTruck")
    #     Deployment_Infantry = self.load_xlsx_deploy("Deployment_Infantry")
    #     Deployment_ShipboardCombat_plane = self.load_xlsx_deploy("Deployment_ShipboardCombat_plane")
    #     Deployment_HeavyDestroyer_ShipID = []
    #
    #     # 保持顺序的部署算子类型，以便调试。0909xxh
    #     WheeledCombatTruck_ZB200ID = []
    #     MissleTruckID = []
    #     MainBattleTank_ZTZ200ID = []
    #     HeavyDestroyer_ShipID = []
    #     InfantryID = []
    #     ShipboardCombat_planeID = []
    #
    #     for i in range(16):  # 确定序号以测试开火。
    #         MainBattleTank_ZTZ200ID.append("MainBattleTank_ZTZ200_" + str(i))
    #     for i in range(len(Deployment_MissleTruck)):  # 确定序号以测试开火。
    #         MissleTruckID.append("missile_truck" + str(i+2)) # 这个是红蓝方混编的。麻了。要根据json改。
    #     for i in range(len(Deployment_WheeledCombatTruck_ZB200)):
    #         WheeledCombatTruck_ZB200ID.append("WheeledCmobatTruck_ZB200_"+str(i))
    #     for i in range(len(Deployment_Infantry)):
    #         InfantryID.append("Infantry" + str(i+2))
    #     for i in range(len(Deployment_ShipboardCombat_plane)):
    #         ShipboardCombat_planeID.append("ShipboardCombat_plane"+str(i+1))
    #
    #     self.mb = MainBattleTank_ZTZ200ID # 主战坦克
    #     self.whc = WheeledCombatTruck_ZB200ID # 轮式步战车
    #     self.m = MissleTruckID # DDFS车
    #     self.iftr = InfantryID # 步兵班
    #     self.hd = HeavyDestroyer_ShipID # 驱逐舰
    #
    #     # 配合自动调试的修改，xxh0909
    #     try:
    #         # 配合自动调试的修改，xxh0909
    #         Deployment_MainBattleTank_ZTZ200, Deployment_MissleTruck, Deployment_WheeledCombatTruck_ZB200, \
    #         Deployment_Infantry, Deployment_HeavyDestroyer_ShipID \
    #         = self.deploy_modify_location(Deployment_MainBattleTank_ZTZ200, Deployment_MissleTruck,Deployment_WheeledCombatTruck_ZB200,
    #                                     Deployment_Infantry, Deployment_HeavyDestroyer_ShipID)
    #     except:
    #         print("XXHtest: auto kaihuo test disabled")
    #
    #     for i in range(len(MainBattleTank_ZTZ200ID)):
    #         self._ArmorCar_Deploy_Action(MainBattleTank_ZTZ200ID[i], Deployment_MainBattleTank_ZTZ200[i][0],
    #                                             Deployment_MainBattleTank_ZTZ200[i][1],
    #                                             Deployment_MainBattleTank_ZTZ200[i][2], Deployment_MainBattleTank_ZTZ200[i][3],
    #                                             Deployment_MainBattleTank_ZTZ200[i][4])
    #
    #     for i in range(len(WheeledCombatTruck_ZB200ID)):
    #         self._Deploy_Action(WheeledCombatTruck_ZB200ID[i], Deployment_WheeledCombatTruck_ZB200[i][0],
    #                                             Deployment_WheeledCombatTruck_ZB200[i][1],
    #                                             Deployment_WheeledCombatTruck_ZB200[i][2])
    #     for i in range(len(MissleTruckID)):
    #         self._Deploy_Action(MissleTruckID[i], Deployment_MissleTruck[i][0],
    #                                             Deployment_MissleTruck[i][1],
    #                                             Deployment_MissleTruck[i][2])
    #     for i in range(len(InfantryID)):
    #         self._Deploy_Action(InfantryID[i], Deployment_Infantry[i][0],
    #                                             Deployment_Infantry[i][1],
    #                                             Deployment_Infantry[i][2])
    #
    #     for i in range(len(ShipboardCombat_planeID)):
    #         self._Deploy_Action(ShipboardCombat_planeID[i], Deployment_ShipboardCombat_plane[i][0],
    #                                             Deployment_ShipboardCombat_plane[i][1],
    #                                             Deployment_ShipboardCombat_plane[i][2],
    #                             )
    #     return self.act

    def deploy(self, Ids):
        #部署指令
        self.act = []

        Deployment_MainBattleTank_ZTZ200 = [[2.68984, 39.70, 0, 30, 30], [2.68984, 39.70, 0, 30, 30],
                                            [2.68984, 39.70, 0, 30, 30],
                                            [2.68984, 39.70, 0, 30, 30],
                                            ]
        # 两个突击车
        Deployment_WheeledCombatTruck_ZB200 = [[2.68818, 39.7026, 0], [2.68818, 39.7026, 0],
                                               [2.68818, 39.7026, 0],
                                               [2.68818, 39.7026, 0],
                                               ]
        Deployment_MissleTruck = [[2.68995, 39.7, 0], [2.68995, 39.7, 0], [2.68995, 39.7, 0], [2.68995, 39.7, 0],
                                  [2.68995, 39.7, 0],
                                  ]
        Deployment_Infantry = [[2.68618, 39.7006, 0], [2.68618, 39.7006, 0],
                               [2.68618, 39.7006, 0],
                               [2.68618, 39.7006, 0],
                               ]
        Deployment_ShipboardCombat_plane = [[2.68995, 39.7, 1500]]

        MainBattleTank_ZTZ200ID = [id for id in Ids if "MainBattleTank_ZTZ200" in id]
        MainBattleTank_ZTZ200ID.sort()
        WheeledCmobatTruck_ZB200ID = [id for id in Ids if "WheeledCmobatTruck_ZB200" in id]
        WheeledCmobatTruck_ZB200ID.sort()
        MissleTruckID = [id for id in Ids if "missile_truck" in id]
        MissleTruckID.sort()
        InfantryID = [id for id in Ids if "Infantry" in id and "Bullet_ZT" not in id]
        InfantryID.sort()
        HeavyDestroyer_ShipID = [id for id in Ids if "HeavyDestroyer_Ship" in id]
        HeavyDestroyer_ShipID.sort()
        ShipboardCombat_planeID = [id for id in Ids if "ShipboardCombat_plane" in id]  # 无人查打一体机，添加
        ShipboardCombat_planeID.sort()

        self.mb = MainBattleTank_ZTZ200ID # 主Zh坦克
        self.whc = WheeledCmobatTruck_ZB200ID # 轮式步战车
        self.m = MissleTruckID # DDFS车
        self.iftr = InfantryID # 步兵班
        self.sbc = ShipboardCombat_planeID  # 无人查打

        for i in range(len(self.mb)):
            self._ArmorCar_Deploy_Action(self.mb[i], Deployment_MainBattleTank_ZTZ200[i][0],
                                                Deployment_MainBattleTank_ZTZ200[i][1],
                                                Deployment_MainBattleTank_ZTZ200[i][2], Deployment_MainBattleTank_ZTZ200[i][3],
                                                Deployment_MainBattleTank_ZTZ200[i][4])
        for i in range(len(self.whc)):
            self._Deploy_Action(self.whc[i], Deployment_WheeledCombatTruck_ZB200[i][0],
                                                Deployment_WheeledCombatTruck_ZB200[i][1],
                                                Deployment_WheeledCombatTruck_ZB200[i][2])
        for i in range(len(self.m)):
            self._Deploy_Action(self.m[i], Deployment_MissleTruck[i][0],
                                                Deployment_MissleTruck[i][1],
                                                Deployment_MissleTruck[i][2])

        for i in range(len(self.iftr)):
            self._Deploy_Action(self.iftr[i], Deployment_Infantry[i][0],
                                                Deployment_Infantry[i][1],
                                                Deployment_Infantry[i][2])
        for i in range(len(self.sbc)):
            self._Deploy_Action(self.sbc[i], Deployment_ShipboardCombat_plane[i][0],
                                Deployment_ShipboardCombat_plane[i][1],
                                Deployment_ShipboardCombat_plane[i][2],
                                )


        return self.act

    def Weapon_estimate(self, status, ID, missileType):  # 判断D是否耗尽
        type = True
        for i in range(len(status[ID]["WeaponState"])):
            if status[ID]["WeaponState"][i]['WeaponType'] == missileType and \
                    status[ID]["WeaponState"][0]['WeaponNum'] == 0:
                type = False
        return type

    def step(self, status):
        self.status = status
        self.num += 1
        self.act = []
        # 装备移动
        print(self.num)
        print("blue agent")
        self.detected_state = self.get_detect_info(self.status)

        if len(self.detected_state) > 2:
            print("tance daole")

        if self.num == 1:
            self.Inint_abstract_state(self.status)  # 别的先就地隐蔽起来

        # 前面是测试代码。
        # =======================================================
        # 后面是正经（？）策略。
        # self.step1()
        # self.step1_1()
        # self.step1_2()
        # self.step1_3()
        # self.step1_31()
        self.step1_32()
        # self.step2()
        # self.step3()

        # 兼容性，把Gostep放在这里面了
        self.Gostep_abstract_state()

        return self.act

    def step1(self):
        # 第一个全流程的，但是高度依赖于初始部署。
        target_LLA = [2.71, 39.76, 0]
        # target_LLA = [2.65, 39.7, 0]
        run_LLA = [2.75, 39.80, 0]

        if self.num == 1:
            # 先上车
            self.Inint_abstract_state(self.status)  # 别的先就地隐蔽起来
            ZB200_status = self.select_by_type("WheeledCmobatTruck_ZB200")
            bin_status = self.select_by_type("Infantry")
            InfantryID = list(bin_status.keys())
            WheeledCombatTruck_ZB200ID = list(ZB200_status.keys())

            self.set_none(ZB200_status)  # 这个先关了一下
            self.set_none(bin_status)  # 这个先关了一下

            for i in range(len(WheeledCombatTruck_ZB200ID)):
                self._On_Board_Action(WheeledCombatTruck_ZB200ID[i], InfantryID[i])

            self.last_order_num = self.num

        if (self.num >= 5) and (self.num <= 10):
            # 到这应该算是上车完成了。保险起见再检测一下
            shishi_Infantry_status = self.select_by_type("Infantry")
            if (len(shishi_Infantry_status) == 0) or (self.num == 10):
                # 那说明上车成功了。
                # 先A到附近去结阵。
                target_LLA_near = [target_LLA[0] + 0.01, target_LLA[1] + 0.01, 0]
                self.group_A(target_LLA_near, status=self.status)
                self.last_order_num = self.num

        if (self.num >= 100) and (self.num <= 105):
            if self.check_all_finished() or (self.num == 105):
                ZB200_status = self.select_by_type("WheeledCmobatTruck_ZB200")
                WheeledCombatTruck_ZB100ID = list(ZB200_status.keys())
                self.set_none(ZB200_status)  # 这个先关了一下

                for i in range(len(WheeledCombatTruck_ZB100ID)):
                    self._Off_Board_Action(WheeledCombatTruck_ZB100ID[i])

                self.last_order_num = self.num

        # 然后A过去，就放在那里。
        if (self.num > 105) and (self.num <= 205):
            if self.check_all_finished() or (self.num == 205):
                tank_status = self.select_by_type("MainBattleTank")
                xiaoche_status = self.select_by_type("Truck")
                jidong_status = {}
                jidong_status.update(tank_status)
                jidong_status.update(xiaoche_status)
                # 机动部队A过去
                self.group_A(target_LLA, status=jidong_status)
                self.last_order_num = self.num

        # 然后就新常态了。
        if self.num > 205:
            # 先探测一下，如果有合适的就直接结阵A过去
            self.detected_state = self.get_detect_info(self.status)

            tank_status = self.select_by_type("MainBattleTank")
            xiaoche_status = self.select_by_type("Truck")
            jidong_status = {}
            jidong_status.update(tank_status)
            jidong_status.update(xiaoche_status)
            # 这两个恐怕不要A到太近的地方
            bin_status = self.select_by_type("Infantry")
            daodan_status = self.select_by_type("missile_truck")

            if len(self.detected_state) > 2 :
                # 那就是探测到东西了，咬它！
                if len(jidong_status) > 0 :
                    attacker_ID = list(jidong_status.keys())[0]
                    target_ID_local, target_LLA_local, target_distance_local \
                        = self.range_estimate2(attacker_ID, self.detected_state)
                    if not("ShipboardCombat" in target_ID_local):
                        # 只出动机动力量.
                        self.group_A(target_LLA_local, status=jidong_status)

                # 防御力量不动，但是开火，嘎嘎乱杀。
                for attacker_ID in daodan_status:
                    self.set_open_fire(attacker_ID)
                daodan_list = list(daodan_status.keys())

                if len(daodan_list) > 0:
                    self.set_follow_and_defend(bin_status, daodan_list[0])
                else:
                    self.group_A(target_LLA, status=bin_status)
                last_order_num = self.num
            else:
                # 那就是没探测到东西，那就A回去，不要在外面逗留
                self.group_A(target_LLA, status=jidong_status)
                last_order_num = self.num

    def step1_1(self):
        # 第一个全流程的，但是高度依赖于初始部署。
        target_LLA = [2.71, 39.76, 0]
        # target_LLA = [2.65, 39.7, 0]
        run_LLA = [2.75, 39.80, 0]

        if self.num == 1:
            # 先上车
            self.Inint_abstract_state(self.status)  # 别的先就地隐蔽起来
            ZB200_status = self.select_by_type("WheeledCmobatTruck_ZB200")
            bin_status = self.select_by_type("Infantry")
            InfantryID = list(bin_status.keys())
            WheeledCombatTruck_ZB200ID = list(ZB200_status.keys())

            self.set_none(ZB200_status)  # 这个先关了一下
            self.set_none(bin_status)  # 这个先关了一下

            for i in range(len(WheeledCombatTruck_ZB200ID)):
                self._On_Board_Action(WheeledCombatTruck_ZB200ID[i], InfantryID[i])

            self.last_order_num = self.num

        if (self.num >= 5) and (self.num <= 10):
            # 到这应该算是上车完成了。保险起见再检测一下
            shishi_Infantry_status = self.select_by_type("Infantry")
            if (len(shishi_Infantry_status) == 0) or (self.num == 10):
                # 那说明上车成功了。
                # 先A到附近去结阵。
                target_LLA_near = [target_LLA[0] - 0.01, target_LLA[1] + 0.01, 0]
                self.group_A(target_LLA_near, status=self.status)
                self.last_order_num = self.num

        if (self.num >= 300) and (self.num <= 305):
            if self.check_all_finished() or (self.num == 305):
                ZB200_status = self.select_by_type("WheeledCmobatTruck_ZB200")
                WheeledCombatTruck_ZB100ID = list(ZB200_status.keys())
                self.set_none(ZB200_status)  # 这个先关了一下

                for i in range(len(WheeledCombatTruck_ZB100ID)):
                    self._Off_Board_Action(WheeledCombatTruck_ZB100ID[i])

                self.last_order_num = self.num

        # 然后A过去，就放在那里。
        if (self.num > 305) and (self.num <= 405):
            if self.check_all_finished() or (self.num == 305):
                tank_status = self.select_by_type("MainBattleTank")
                xiaoche_status = self.select_by_type("Truck")
                feiji_status = self.select_by_type("Ship")
                jidong_status = {}
                jidong_status.update(tank_status)
                jidong_status.update(xiaoche_status)
                jidong_status.update(feiji_status)
                # 机动部队A过去
                self.group_A(target_LLA, status=jidong_status)
                self.last_order_num = self.num

        # 然后就新常态了。
        if self.num > 405:
            # 先探测一下，如果有合适的就直接结阵A过去
            self.detected_state = self.get_detect_info(self.status)

            tank_status = self.select_by_type("MainBattleTank")
            xiaoche_status = self.select_by_type("Truck")
            feiji_status = self.select_by_type("Ship")
            jidong_status = {}
            jidong_status.update(tank_status)
            jidong_status.update(xiaoche_status)
            jidong_status.update(feiji_status)
            # 这两个恐怕不要A到太近的地方
            bin_status = self.select_by_type("Infantry")
            jidong_status.update(bin_status)
            daodan_status = self.select_by_type("missile_truck")

            if len(self.detected_state) > 2 and len(self.detected_state) < 10 :
                # 那就是探测到东西了，咬它！
                if len(jidong_status) > 0 :
                    attacker_ID = list(jidong_status.keys())[0]
                    target_ID_local, target_LLA_local, target_distance_local \
                        = self.range_estimate2(attacker_ID, self.detected_state)
                    if not("ShipboardCombat" in target_ID_local):
                        # 只出动机动力量.
                        self.group_A(target_LLA_local, status=jidong_status)

                # 防御力量不动，但是开火，嘎嘎乱杀。
                for attacker_ID in daodan_status:
                    self.set_open_fire(attacker_ID)
                daodan_list = list(daodan_status.keys())

                # if len(daodan_list) > 0:
                #     self.set_follow_and_defend(bin_status, daodan_list[0])
                # else:
                #     self.group_A(target_LLA, status=bin_status)

                last_order_num = self.num
            else:
                # 那就是没探测到东西，那就A回去，不要在外面逗留
                self.group_A(target_LLA, status=jidong_status)
                # self.group_D(status=self.status)
                last_order_num = self.num

    def step1_2(self):
        # 这个就用来打taichu吧
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

        target_LLA = [2.71, 39.76, 70]
        # target_LLA = [2.65, 39.7, 0]
        run_LLA = [2.715, 39.75, 70]

        target_LLA = [2.71, 39.76, 70]
        xiache_LLA = [2.657, 39.70, 480]
        # xiache_LLA = [2.65, 39.71, 300]

        if (self.num == 1) :
            self.group_D(status=self.status)
            self.F2A(target_LLA, status=daodan_status)
            self.group_A2(xiache_LLA, che_status, bin_status)
        if (self.num>20) and (self.num<=600): # 测试一下直接A过去能不能打过。
            jidong_status = {}
            if (self.num>250) and (self.num%25):
                jidong_status.update(che_status)
                jidong_status.update(bin_status)
                ave_LLA = self.get_LLA_ave(jidong_status)
                target_LLA = ave_LLA
                self.group_A_gai_reset()
            jidong_status.update(tank_status)
            jidong_status.update(feiji_status)
            self.group_A_gai(xiache_LLA, jidong_status)
            if self.num == 600:
                self.group_A_gai_reset()

        if (self.num>600) and (self.num<=2000):
            # 第一波团打完了，回去接了剩下的步兵然后走
            jidong_status = {}
            jidong_status.update(tank_status)
            jidong_status.update(feiji_status)
            jidong_status.update(che_status)
            # jidong_status.update(bin_status)
            # if (len(bin_status)==0): # 上个毛车，不上了，冲
            #     jidong_status.update(che_status)
            #     jidong_status.update(bin_status)
            # else:
            #     self.group_A2(target_LLA, che_status, bin_status)
            bushu = 1500
            if self.num < bushu:
                self.group_A_gai(target_LLA, jidong_status)
            elif self.num==bushu :
                self.group_A_gai_reset()
                self.group_A(target_LLA, status= jidong_status)
            self.group_A(target_LLA, status=bin_status)
            if self.num == 600:
                self.group_A_gai_reset()
        elif self.num == 2500:
            # A过去
            target_LLA = [2.71, 39.76, 70]
            self.F2A(target_LLA)
        elif self.num == 2900:
            # A过去
            target_LLA = [2.71, 39.76, 70]
            self.F2A(target_LLA)

        return

        if (self.num ==1) and (self.num <= 455):
            # 先上车,A过去。
            jidong_status = {}
            # jidong_status.update(tank_status)
            # jidong_status.update(xiaoche_status)
            # jidong_status.update(feiji_status)
            self.group_A2(xiache_LLA, che_status, bin_status)
            jidong_status.update(che_status)
            jidong_status.update(bin_status)
            self.group_D(status=bin_status)

            self.group_A(target_LLA, status=jidong_status)
            # self.group_A_gai(target_LLA, jidong_status)

            self.group_A(xiache_LLA, status=feiji_status)
            self.F2A(target_LLA, status=daodan_status)
            self.last_order_num = self.num

        #
        # if (self.num > 10) and (self.num <= 455):
        #     target_LLA =[2.63, 39.74, 70]
        #     self.group_A_gai(target_LLA, tank_status)
        #     if self.num == 455:
        #         self.group_A_gai_reset()

        # 然后就新常态了。防守某个点
        target_LLA = [2.72, 39.78, 70]
        if (self.num>2000):
            target_LLA = [2.71, 39.76, 70]
        if (self.num > 455) and (self.num <= 2500):
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
                        # target_LLA = [2.71+0.008, 39.76+0.008, 70]
                        self.group_A(target_LLA, status=daodan_status) # 这个跑路
                        self.last_order_num = self.num
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
        elif self.num == 2900:
            # A过去
            target_LLA = [2.71, 39.76, 70]
            self.F2A(target_LLA)

    def step1_3(self):
        # 这个是用来通用性地打别的队的。
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

        target_LLA = [2.71, 39.76, 70]
        # target_LLA = [2.65, 39.7, 0]
        run_LLA = [2.715, 39.75, 70]

        target_LLA = [2.71, 39.76, 70]
        xiache_LLA = [2.705, 39.76, 70]
        # xiache_LLA = [2.65, 39.71, 300]

        if (self.num == 1) :
            self.group_D(status=self.status)
            self.F2A(target_LLA, status=daodan_status)
            self.group_A2(xiache_LLA, che_status, bin_status)
        if (self.num>20) and (self.num<=600): # 直接结阵A到点里去好了呢。
            jidong_status = {}
            if (self.num>455) and (self.num%25):
                jidong_status.update(che_status)
                jidong_status.update(bin_status)
                ave_LLA = self.get_LLA_ave(jidong_status)
                target_LLA = ave_LLA
                self.group_A_gai_reset()
            jidong_status.update(tank_status)
            jidong_status.update(feiji_status)
            self.group_A_gai(xiache_LLA, jidong_status)
            if self.num == 600:
                self.group_A_gai_reset()

        # 然后就新常态了。防守某个点
        if (self.num > 455) and (self.num <= 2500):
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
                        # target_LLA = [2.71+0.008, 39.76+0.008, 70]
                        self.group_A(target_LLA, status=daodan_status) # 这个跑路
                        self.last_order_num = self.num
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
        elif self.num == 2900:
            # A过去
            target_LLA = [2.71, 39.76, 70]
            self.F2A(target_LLA)

    def step1_31(self):
        # 这个是用来通用性地打别的队的。疯狂A进去抢点
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

        target_LLA = [2.71, 39.76, 70]
        # target_LLA = [2.65, 39.7, 0]
        run_LLA = [2.715, 39.75, 70]

        target_LLA = [2.71, 39.76, 70]
        xiache_LLA = [2.705, 39.76, 70]
        # xiache_LLA = [2.65, 39.71, 300]

        if (self.num == 1) :
            self.group_A(target_LLA, status=daodan_status)
            self.group_A2(xiache_LLA, che_status, bin_status)
            self.group_A(target_LLA, status=jidong_status)

        # 然后就新常态了。防守某个点
        if (self.num > 455) and (self.num <= 3000):
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
                        # self.group_A(target_LLA, status=daodan_status)
                    self.last_order_num = self.num
                    pass
                else:
                    # 那就是没探测到东西，那就A回去，不要在外面逗留
                    pass
            if self.num % 200 == 10:
                self.group_A(target_LLA, status = jidong_status)
        if ((self.num % 20 ==10) or (self.flag_zhandian == False)) and (self.num > 100):
            self.group_zhandian(self.status, target_LLA = [2.71, 39.76, 90])

    def step1_32(self):
        # 这个是用来通用性地打别的队的。防空车不要进去送
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

        target_LLA = [2.71, 39.76, 70]
        # target_LLA = [2.65, 39.7, 0]
        run_LLA = [2.778, 39.795, 1000]

        target_LLA = [2.71, 39.76, 70]
        xiache_LLA = [2.705, 39.76, 70]
        # xiache_LLA = [2.65, 39.71, 300]

        if (self.num == 1) :
            # self.group_A(target_LLA, status=daodan_status)
            self.group_A(run_LLA, status=daodan_status)
            self.group_A2(xiache_LLA, che_status, bin_status)
            self.group_A(target_LLA, status=jidong_status)

        # 然后就新常态了。防守某个点
        if (self.num > 455) and (self.num <= 3000):
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
                        # self.group_A(target_LLA, status=daodan_status)
                    self.last_order_num = self.num
                    pass
                else:
                    # 那就是没探测到东西，那就A回去，不要在外面逗留
                    pass
            if self.num % 200 == 10:
                self.group_A(target_LLA, status = jidong_status)
                self.group_A(run_LLA, status = daodan_status)
        if ((self.num % 20 ==10) or (self.flag_zhandian == False)) and (self.num > 100):
            self.group_zhandian(self.status, target_LLA = [2.71, 39.76, 90])
            if (self.num>1500) and self.num % 200 == 10:
                # 后期要是打不过就狗起来，别去送了。
                self.group_A(run_LLA, status=daodan_status)


    def step2(self):
        # 用来合的，先解决“有没有打起来”的一个
        point_LLA = np.array([2.71, 39.76, 0])
        # target_LLA = [2.65, 39.7, 0]
        run_LLA = np.array([2.77, 39.87, 0])

        d_LLA = run_LLA - point_LLA

        # 现在还没有自动打车，所以先A到一个点去再说
        if self.num == 1:
            self.group_A(run_LLA)

        if self.num == 500:
            # target_LLA = run_LLA + d_LLA  # 本来想多分几段，后来想想好像也没有什么必要。
            # self.group_A(target_LLA)

            tank_status = self.select_by_type("MainBattleTank")
            xiaoche_status = self.select_by_type("Truck")
            jidong_status = {}
            jidong_status.update(tank_status)
            jidong_status.update(xiaoche_status)
            self.group_A(point_LLA, status=jidong_status)

            # 防御力量慢点动，但是开火，嘎嘎乱杀。
            bin_status = self.select_by_type("Infantry")
            daodan_status = self.select_by_type("missile_truck")
            target_LLA = run_LLA + d_LLA / 2
            self.group_A(target_LLA, status=daodan_status)
            daodan_list = list(daodan_status.keys())
            self.set_follow_and_defend(bin_status, daodan_list[0])  # 保卫一个，没啥不好的。
            last_order_num = self.num

        # 然后就新常态了。
        if self.num > 550:
            # 先探测一下，如果有合适的就直接结阵A过去
            self.detected_state = self.get_detect_info(self.status)
            # 只出动机动力量,
            tank_status = self.select_by_type("MainBattleTank")
            xiaoche_status = self.select_by_type("Truck")
            jidong_status = {}
            jidong_status.update(tank_status)
            jidong_status.update(xiaoche_status)
            if len(self.detected_state) > 0 :
                # 那就是探测到东西了，咬它！
                tank_status = self.select_by_type("MainBattleTank")
                xiaoche_status = self.select_by_type("Truck")
                attacker_ID = list(tank_status.keys())[0]

                if not("ShipboardCombat" in self.target_ID_local):
                    target_ID_local, target_LLA_local, target_distance_local \
                        = self.range_estimate2(attacker_ID, self.detected_state)
                    # 只出动机动力量
                    tank_status = self.select_by_type("MainBattleTank")
                    xiaoche_status = self.select_by_type("Truck")
                    jidong_status = {}
                    jidong_status.update(tank_status)
                    jidong_status.update(xiaoche_status)
                    self.group_A(target_LLA_local, status=jidong_status)

                # 防御力量不动，但是开火，嘎嘎乱杀。
                bin_status = self.select_by_type("Infantry")
                daodan_status = self.select_by_type("missile_truck")
                self.set_open_fire(daodan_status)
                daodan_list = list(daodan_status.keys())
                self.set_follow_and_defend(bin_status, daodan_list[0])  # 保卫一个，没啥不好的。
                self.last_order_num = self.num
            else:
                # 那就是没探测到东西，那就A回去，不要在外面逗留
                self.group_A(point_LLA, status=jidong_status)
                self.last_order_num = self.num

    def step3(self):
        # 这个是用来测试的。
        target_LLA = np.array([2.71, 39.76, 0])
        point_LLA = np.array([2.68, 39.70, 200])
        xiaoche_status = self.select_by_type("Truck")
        tank_status = self.select_by_type("Tank")
        if self.num == 48:
            print("彳亍")
        if self.num == 1:
            # self.set_circle(xiaoche_status, point_LLA, R=0.001)
            # self.set_circle(tank_status, point_LLA, R=0.0005)
            self.set_circle("WheeledCmobatTruck_ZB200_0", point_LLA, R=0.01)
            # self._Move_Action("WheeledCmobatTruck_ZB200_0", point_LLA[0], point_LLA[1], point_LLA[2])
            # self.set_move_and_attack(xiaoche_status, point_LLA)
        if (self.num % 20 == 5) :
            self.group_zhandian(tank_status, target_LLA = target_LLA)

    def checkNumMissle(self, state, shipID, missletype='ShipToShip_missile'):
        if missletype in state[shipID]['WeaponState'][0]['WeaponID']:
            return state[shipID]['WeaponState'][0]['WeaponNum']
        else:
            return state[shipID]['WeaponState'][1]['WeaponNum']

    def deploy_modify_set(self,my_unit_type, my_weapon_type, target_unit_type, location = [2.6801, 39.70, 0], index = 0 ):
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
            print('blue_agent: deploy_modify enabled')
            for i in range(len(self.name_list)):
                if self.name_list[i] in self.modify_unit_type:
                    for j in range(3):
                        args[i][0][j] = self.modify_location[j]

        # # 把那两个测AOE的步兵也弄到目标位置
        # for j in range(3):
        #     args[3][3][j] = self.modify_location[j]
        #     args[3][4][j] = self.modify_location[j]
        # args[3][3][0] = args[3][3][0] + 0.00005
        # args[3][4][0] = args[3][4][0]

        # 减少了装备数量之后程序得改否则就不对力
        for j in range(3):
            args[3][1][j] = self.modify_location[j]
            args[3][2][j] = self.modify_location[j]
        args[3][1][0] = args[3][3][0] + 0.00005
        args[3][2][0] = args[3][4][0]
        return args

    def deploy_modify_getstate(self, state):
        # enum
        # VehicleMoveState
        # {
        #     move, // 移动
        # stay, // 停止
        # hidden // 掩蔽
        # };
        self.modify_state = state
        return 0

    def deploy_modify_attack(self):
        # 组装一个攻击命令，用来操作。
        ID_attacker = self.modify_unit_type + '_' + str(self.modify_index)
        # 攻击坐标就硬编码了先
        self._Attack_Action(ID_attacker, 2.68, 39.701, 390, self.modify_weapon_type)
        return 0

    def deploy_modify_setstate(self, time_step):
        # 这个按道理说只用发一次，但是保险起见，还是隔一段时间就发一次好了。
        if (time_step%20==2):
            if (self.modify_unit_type == self.name_list[1])or(self.modify_unit_type == self.name_list[3]):
                ID_target = self.modify_unit_type + str(self.modify_index+8) # 导弹车和步兵的编号方式不一样
            else:
                ID_target = self.modify_unit_type + '_' + str(self.modify_index)
            self._Change_State(ID_target, self.modify_state)

        return 0