# 这个是agent.py先占着位置，用于把程序的其他地方调好。

import math
import copy
import numpy as np
import codecs
import sys, os
import xlrd
import time
from enum import Enum
from agent_guize.base_agent import BaseAgent
import queue
        
class Agent(object):
    def __init__(self):
        self.infantry_tank_map = {}
        self.groupmap = {}
        self.act = []
        self.time_ = time.time()

        # 以下xxh定制，不保熟
        self.abstract_state = {}  # key 是装备ID，value是抽象状态
        # 抽象状态目前设想这几种，移动攻击、隐藏警戒、跟踪追击、巡逻侦察、自由开火、跟随己方单位。再加一个“不用”。
        # 再加一个，步兵车加一个冲锋下车好了。
        # ["move_and_attack", "hidden_and_alert", "track_and_attack",
        # "partrol_and_monitor", "follow_and_defend", "open_fire", "none", "charge_and_xiache"]
        self.deploy_folder = ""
        self.weapon_list = ["HighExplosiveShot_ZT", "HighExplosiveShot", "ShortRangeMissile", "RPG", "AGM",
                            "ArmorPiercingShot_ZT", "ArmorPiercingShot", "Bullet_ZT", "bullet"]
        # 这个是有优先级顺序的。zt的放在不zt的前面，否则不对。因为后面是从前往后遍历。
        # self.landform_list = landform_type()
        self.landform_list = ["construction", "forest", "river", "covered_road", "open_area",
                              "default"]  # 这个也是有优先顺序的，看哪些比较好

        self.detected_state = {}
        self.detected_state2 = {}  # 这个预计用于折腾什么路径规划啊那些。就key是ID，value是观测到的不同帧数的路径好了。
        # 就只存两帧，多的不要。
        self.group_A_gai_config = {"target_LLA": [],
                                   "start_LLA": [],
                                   "target_LLA_next": [],
                                   "flag_start": False,
                                   "flag_end": False,
                                   "dL": 0.008,
                                   "dl_vector": []}
        self.weapon_V = {"HighExplosiveShot_ZT": 1200, "HighExplosiveShot": 1000,
                         "ShortRangeMissile": 1800, "RPG": 245, "AGM": 680,
                         "ArmorPiercingShot_ZT": 1700, "ArmorPiercingShot": 1500,
                         "Bullet_ZT": 840, "bullet": 600}
        self.flag_zhandian = False

        self.commands_queue = queue.Queue(maxsize=114514) # 这个是新加的，用来处理和大模型的交互。

    def LLA2XYZ(self, lon, lat, alt):
        Earthe = 0.0818191908426
        Radius_Earth = 6378140.0
        PI = 3.14159265358979
        deg2rad = PI / 180.0
        lat = lat * deg2rad
        lon = lon * deg2rad
        omge = 0.99330562000987
        d = Earthe * math.sin(lat)
        n = Radius_Earth / math.sqrt(1 - math.pow(d, 2))
        nph = n + alt
        x = nph * math.cos(lat) * math.cos(lon)
        y = nph * math.cos(lat) * math.sin(lon)
        z = (omge * n + alt) * math.sin(lat)
        return x, y, z

    def XYZ2LLA(self, x, y, z):
        Radius_Earth = 6378140
        Oblate_Earth = 1.0 / 298.257
        a = Radius_Earth
        b = a * (1 - Oblate_Earth)
        e = math.sqrt(1 - math.pow(b / a, 2))
        x2 = x * x
        y2 = y * y
        root = math.sqrt(x2 + y2)
        e2 = e * e
        error = 1.0
        d = 0.0
        B = 0.0
        H = 0.0
        eps = 1e-10
        PI = 3.14159265358979
        deg2rad = PI / 180.0
        rad2deg = 180.0 / PI

        while error >= eps:
            temp = d
            B = math.atan(z / root / (1 - d))
            sin2B = math.sin(B) * math.sin(B)
            N = a / math.sqrt(1 - e2 * sin2B)
            H = root / math.cos(B) - N
            d = N * e2 / (N + H)
            error = abs(d - temp)
        lat = B
        alt = H
        temp = math.atan(y / x)
        if x >= 0:
            lon = temp
        elif ((x < 0) and (y >= 0)):
            lon = PI + temp
        else:
            lon = temp - PI
        lat = lat * rad2deg
        lon = lon * rad2deg
        alt = alt
        return lon, lat, alt

    def distance(self, lon1, lat1, alt1, lon2, lat2, alt2):
        x1, y1, z1 = self.LLA2XYZ(lon1, lat1, alt1)
        x2, y2, z2 = self.LLA2XYZ(lon2, lat2, alt2)
        x2tox1 = x2 - x1
        y2toy1 = y2 - y1
        z2toz1 = z2 - z1
        distance = math.sqrt(x2tox1 * x2tox1 + y2toy1 * y2toy1 + z2toz1 * z2toz1)
        return distance

    # 装甲车部署指令函数
    # TODO: 高度、地理信息；改接口
    def _ArmorCar_Deploy_Action(self, id, lon, lat, alt, PierceShotNum, ExplosiveShotNum):
        ArmorCarDeployAction = {"Type": "ArmorCar_Deploy", "Id": id, "Lon": lon, "Lat": lat, "Alt": alt,
                                "PierceShotNum": PierceShotNum, "ExplosiveShotNum": ExplosiveShotNum}
        self.act.append(ArmorCarDeployAction)
        return ArmorCarDeployAction

    # 非装甲单位部署指令
    def _Deploy_Action(self, id, lon, lat, alt):
        DeployAction = {"Type": "Deploy", "Id": id, "Lon": lon, "Lat": lat, "Alt": alt}
        self._exec_group_cmd(id, "Deploy", **DeployAction)
        # print(DeployAction)
        return DeployAction

    # 移动指令函数
    def _Move_Action(self, Id, lon, lat, alt):
        MoveAction = {"Type": "Move", "Id": Id, "Lon": lon, "Lat": lat, "Alt": alt}
        # self._exec_group_cmd(Id, "Move", **MoveAction)
        self.act.append(MoveAction)  # xxh0906
        return MoveAction

    def _Change_State(self, Id, vehicleMoveState):
        ChangeState = {"Type": "Change", "Id": Id, "VehicleMoveState": vehicleMoveState}
        self.act.append(ChangeState)
        return ChangeState

    # 释放飞机指令函数
    def _Plane_Launch_Action(self, Id, Plane_Type, lon, lat, alt):
        planeLaunchAction = {"Type": "Launch_plane", "Id": Id, "Plane_Type": Plane_Type, "Lon": lon, "Lat": lat,
                             "Alt": alt}
        self.act.append(planeLaunchAction)
        return planeLaunchAction

    # 火力分配指令函数
    def _Attack_Action(self, Id, lon, lat, alt, Unit_Type):
        AttackAction = {"Type": "Attack", "Id": Id, "Unit_Type": Unit_Type, "Lon": lon, "Lat": lat, "Alt": alt}
        self._exec_group_cmd(Id, "Attack", **AttackAction)
        return AttackAction

    # 雷达开关机指令函数
    def _Set_Radar_Action(self, Id, On):
        setRadarAction = {"Type": "Set_radar", "Id": Id, "On": On}
        # self._exec_group_cmd(id, "Set_radar", setRadarAction)
        self.act.append(setRadarAction)
        return setRadarAction

    # 编队指令
    def _Combine_Action(self, Id, groupId):
        CombineAction = {"Type": "Combine_", "Id": Id, "groupId": groupId}
        print("command combine")
        self._insert_to_groupmap(Id, groupId)  # groupid 合法性由qt 判断
        print("current group ", self.groupmap)
        self.act.append(CombineAction)
        return CombineAction

    def _Del_Combine_Action(self, groupId):
        DelCombineAction = {"Type": "DelCombine", "groupId": groupId}
        print("command delcombine")
        self._remove_from_groupmap(groupId)
        print("current group ", self.groupmap)
        self.act.append(DelCombineAction)
        return DelCombineAction

    # 上下车指令
    def _On_Board_Action(self, tankid, infantryid):
        onBoardAction = {"Type": "On_Board", "tankid": tankid, "infantryid": infantryid}
        print("On board: ", tankid, infantryid)
        self._insert_to_infantankmap(tankid, infantryid)
        self.act.append(onBoardAction)
        return onBoardAction

    def _Off_Board_Action(self, tankid, infantryid=-1):
        offBoardAction = {"Type": "Off_Board", "tankid": tankid, "infantryid": infantryid}
        print("off board: ", tankid, infantryid)
        self._remove_from_infantrytankmap(tankid, infantryid)
        self.act.append(offBoardAction)
        return offBoardAction

    # szh
    def _insert_to_groupmap(self, unitid, groupid):
        if groupid not in self.groupmap.keys():
            self.groupmap[groupid] = []
        self.groupmap[groupid].append(unitid)
        return

    def _remove_from_groupmap(self, groupid):
        print("in remove from group ", groupid)
        if groupid not in self.groupmap.keys():
            return
        self.groupmap.pop(groupid)
        return

    def _insert_to_infantankmap(self, tankid, infantryid):
        if tankid not in self.infantry_tank_map.keys():
            self.infantry_tank_map[tankid] = []  ##  目前限制步战车上步兵班数量为1
        if tankid in self.infantry_tank_map.keys() and len(self.infantry_tank_map[tankid]) > 0:
            return
        self.infantry_tank_map[tankid].append(infantryid)
        return

    def _remove_from_infantrytankmap(self, tankid, infantryid=-1):
        if tankid not in self.infantry_tank_map.keys():
            return
        else:
            self.infantry_tank_map.pop(tankid)
        return

    # szh
    def _exec_group_cmd(self, unitid, func_type, **kwargs):
        if unitid in self.groupmap.keys():  # 是编队
            print("current group ", self.groupmap)
            print("exec group cmd ", func_type)
            for id_ in self.groupmap[unitid]:
                print("unit in group  ", id_)
                tmpkwargs = copy.deepcopy(kwargs)  # 深拷贝  避免id 变量公用同一个地址
                if "Id" in kwargs.keys():
                    tmpkwargs["Id"] = id_
                self._exec_cmd(id_, func_type, tmpkwargs)
        else:
            # print(kwargs)
            self._exec_cmd(unitid, func_type, kwargs)

    def _exec_cmd(self, id, func_type, kwargs):
        if func_type == 'Attack':  # "Lon": lon, "Lat": lat, "Alt": alt
            # self._Move_Action(kwargs["Id"],kwargs["Lon"] ,kwargs["Lat"], kwargs["Alt"] )
            self.act.append(kwargs)

        elif func_type == "Deploy":  # "Id": id, "Lon": lon, "Lat": lat, "Alt": alt}
            # self._Deploy_Action(kwargs["Id"], kwargs["Lon"], kwargs["Lat"], kwargs["Alt"])
            self.act.append(kwargs)
        elif func_type == "Move":  # "Id": Id, "Lon": lon, "Lat": lat, "Alt": alt}
            # self._Move_Action(kwargs["Id"], kwargs["Lon"], kwargs["Lat"], kwargs["Alt"])
            self.act.append(kwargs)

    def get_detect_info(self, status):
        # LJD不会探测
        filtered_status = self.__status_filter(self.status)
        unitIDList = list(filtered_status.keys())

        detectinfo = dict()
        for unit in unitIDList:
            try:
                for i in range(len(status[unit]['DetectorState'])):
                    for j in range(len(status[unit]['DetectorState'][i]['DetectedState'])):
                        detectinfo[status[unit]['DetectorState'][i]['DetectedState'][j]['targetID']] = \
                            status[unit]['DetectorState'][i]['DetectedState'][j]
            except:
                pass
        return detectinfo

    # xxh尝试整点儿复合命令
    def Gostep_abstract_state(self, **kargs):
        # 这个就用来维护这些复合的抽象命令吧。讲道理，这个直接放在step里面最后一行行吗？好像也没啥不行的。

        # 先更新一遍观测的东西，后面用到再说
        self.detected_state = self.get_detect_info(self.status)
        self.update_detectinfo(self.detected_state)  # 记录一些用于搞提前量的缓存

        # 清理一下abstract_state,被摧毁了的东西就不要在放在里面了.
        abstract_state_new = {}
        filtered_status = self.__status_filter(self.status)
        for attacker_ID in filtered_status:
            if attacker_ID in self.abstract_state:
                try:
                    abstract_state_new[attacker_ID] = self.abstract_state[attacker_ID]
                except:
                    # 这个是用来处理新增加的单位的，主要是用于步兵上下车。
                    abstract_state_new[attacker_ID] = {"abstract_state": "none"}
            else:
                # 下车之后的步兵在filtered_status有在abstract_state没有，得更新进去
                abstract_state_new[attacker_ID] = {}

        self.abstract_state = abstract_state_new

        self.act = []

        # 遍历一下abstract_state，把里面每个单位的命令都走一遍。
        for my_ID in self.abstract_state:
            my_abstract_state = self.abstract_state[my_ID]
            if my_abstract_state == {}:
                # 默认状态的处理
                if ("ArmoredTruck_ZTL100" in my_ID) or ("ShipboardCombat_plane" in my_ID) \
                        or ("WheeledCmobatTruck" in my_ID) or ("MainBattleTank" in my_ID) \
                        or ("missile_truck" in my_ID):
                    # if ("ArmoredTruck_ZTL100" in my_ID) or ("ShipboardCombat_plane" in my_ID):
                    # 对部分装备，如果是空的，就准备好润
                    self.set_partrol_and_monitor(my_ID, self.__get_LLA(my_ID))
                else:
                    # 对别的装备，如果是空的，就隐蔽起来。
                    self.set_hidden_and_alert(my_ID)
            else:
                # 实际的处理
                if my_abstract_state["abstract_state"] == "move_and_attack":
                    # self.__handle_move_and_attack(my_ID, my_abstract_state["target_LLA"])
                    self.__handle_move_and_attack2(my_ID, my_abstract_state["target_LLA"])
                elif my_abstract_state["abstract_state"] == "hidden_and_alert":
                    # self.__handle_hidden_and_alert(my_ID, kargs["GetLandForm"])  # 这个要取地形的，所以要从外面输入GetLandForm函数
                    self.__handle_hidden_and_alert(my_ID)  # 兼容版本的，放弃取地形了。
                elif my_abstract_state["abstract_state"] == "partrol_and_monitor":
                    self.__handle_partrol_and_monitor(my_ID, my_abstract_state["target_LLA"])
                elif my_abstract_state["abstract_state"] == "open_fire":
                    # self.__handle_open_fire(my_ID)
                    self.__handle_open_fire2(my_ID)  # 逻辑升级的open fire
                elif my_abstract_state["abstract_state"] == "follow_and_defend":
                    self.__handle_follow_and_defend(my_ID, my_abstract_state["VIP_ID"],
                                                    my_abstract_state["flag_stand_by"])
                elif my_abstract_state["abstract_state"] == "none":
                    self.__handle_none(my_ID)  # 这个就是纯纯的停止。
                elif my_abstract_state["abstract_state"] == "charge_and_xiache":
                    self.__handle_charge_and_xiache(my_ID, my_abstract_state["infantry_ID"],
                                                    my_abstract_state["target_LLA"], my_abstract_state["flag_state"])
                elif my_abstract_state["abstract_state"] == "circle":
                    self.__handle_circle(my_ID, my_abstract_state["target_LLA"], my_abstract_state["R"])
        return self.act

    def Inint_abstract_state(self, status):
        # 初始化一下，先全都搞成就地隐蔽。
        return
        for my_ID in status:
            # target_LLA = self.__get_LLA(my_ID)
            # self.set_hidden_and_alert(my_ID)
            target_LLA = [2.59, 39.72, 0]
            self.set_partrol_and_monitor(my_ID, target_LLA)

    def set_move_and_attack(self, attacker_ID, target_LLA):
        # 还得是直接用字典，不要整列表。整列表虽然可以整出类似红警的点路径点的效果，但是要覆盖就得额外整东西。不妥
        if (type(attacker_ID) == dict) or (type(attacker_ID) == list):
            # 说明是直接把status输入进来了。那就得循环。
            for attacker_ID_single in attacker_ID:
                self.abstract_state[attacker_ID_single] = {"abstract_state": "move_and_attack",
                                                           "target_LLA": target_LLA,
                                                           "flag_moving": False, "jvli": 114514}
        else:
            self.abstract_state[attacker_ID] = {"abstract_state": "move_and_attack", "target_LLA": target_LLA,
                                                "flag_moving": False, "jvli": 114514}
        pass

    def set_partrol_and_monitor(self, attacker_ID, target_LLA):
        # 这个得动动脑子，微操层面的侦察巡逻，就直接放在这里了.
        if (type(attacker_ID) == dict) or (type(attacker_ID) == list):
            # 说明是直接把status输入进来了。那就得循环。
            for attacker_ID_single in attacker_ID:
                self.abstract_state[attacker_ID_single] = {}
                self.abstract_state[attacker_ID_single] = {"abstract_state": "partrol_and_monitor",
                                                           "attacker_ID": attacker_ID,
                                                           "target_LLA": target_LLA, "flag_arrived": False}
        else:
            self.abstract_state[attacker_ID] = {}
            self.abstract_state[attacker_ID] = {"abstract_state": "partrol_and_monitor", "attacker_ID": attacker_ID,
                                                "target_LLA": target_LLA, "flag_arrived": False}

    def set_hidden_and_alert(self, attacker_ID):
        # 这个就是原地坐下，调成隐蔽状态。
        # 不是原地坐下了，要找周围好的地形。
        if (type(attacker_ID) == dict) or (type(attacker_ID) == list):
            # 说明是直接把status输入进来了。那就得循环。
            for attacker_ID_single in attacker_ID:
                self.abstract_state[attacker_ID_single] = {"abstract_state": "hidden_and_alert", "flag_shelter": False}
        else:
            self.abstract_state[attacker_ID] = {"abstract_state": "hidden_and_alert", "flag_shelter": False}
        pass

    def set_open_fire(self, attacker_ID, target_LLA=[2.71, 39.76, 90]):
        # 这个就是真正意义上的火力全开,全部CD打完,不管别的.
        # 需要一个默认的LLA，没探索到就盲打。
        if (type(attacker_ID) == dict) or (type(attacker_ID) == list):
            # 说明是直接把status输入进来了。那就得循环。
            for attacker_ID_single in attacker_ID:
                self.abstract_state[attacker_ID_single] = {"abstract_state": "open_fire",
                                                           "target_LLA": target_LLA, "flag_runover": False}
        else:
            self.abstract_state[attacker_ID] = {"abstract_state": "open_fire",
                                                "target_LLA": target_LLA, "flag_runover": False}
        pass

    def set_follow_and_defend(self, attacker_ID, VIP_ID):
        if (type(attacker_ID) == dict) or (type(attacker_ID) == list):
            # 说明是直接把status输入进来了。那就得循环。
            for attacker_ID_single in attacker_ID:
                self.abstract_state[attacker_ID_single] = {"abstract_state": "follow_and_defend", "VIP_ID": VIP_ID,
                                                           "flag_stand_by": True}
        else:
            self.abstract_state[attacker_ID] = {"abstract_state": "follow_and_defend", "VIP_ID": VIP_ID,
                                                "flag_stand_by": True}
        pass

    def set_none(self, attacker_ID):
        # 这个就是直接把抽象状态这套关了，设定成不会因为抽象状态而发跟它相关的命令。
        if (type(attacker_ID) == dict) or (type(attacker_ID) == list):
            # 说明是直接把status输入进来了。那就得循环。
            for attacker_ID_single in attacker_ID:
                self.abstract_state[attacker_ID_single] = {"abstract_state": "none"}
        else:
            self.abstract_state[attacker_ID] = {"abstract_state": "none"}
        pass

    def set_charge_and_xiache(self, attacker_ID, infantry_ID, target_LLA):
        # 这个得好好想想有哪些变量。
        # 没在车上就过去接，在车上就A过去，到地方就下车隐蔽，有敌人就下车A它
        # 记录一些状态，没上车且不能上1。没上车且正在上2。在车上且没敌人就3。在车上且有敌人就4。下去打完理论上就1了。
        if (type(attacker_ID) == dict) or (type(attacker_ID) == list):
            # 说明是直接把status输入进来了。那就得循环。
            for attacker_ID_single in attacker_ID:
                self.abstract_state[attacker_ID_single] = {"abstract_state": "charge_and_xiache"}
        else:
            self.abstract_state[attacker_ID] = {"abstract_state": "charge_and_xiache",
                                                "infantry_ID": infantry_ID,
                                                "target_LLA": target_LLA,
                                                "flag_state": 1,
                                                "num_wait": 0}
        pass

    def set_circle(self, attacker_ID, target_LLA, R=0.0009):
        # 临时整个转圈的。这个就不清理next了
        if (type(attacker_ID) == dict) or (type(attacker_ID) == list):
            # 说明是直接把status输入进来了。那就得循环。
            for attacker_ID_single in attacker_ID:
                self.abstract_state[attacker_ID_single] = {"abstract_state": "circle",
                                                           "R":R,
                                                           "point_list": {},
                                                           "index": 0,
                                                           "target_LLA": target_LLA}
        else:
            self.abstract_state[attacker_ID] = {"abstract_state": "circle",
                                                "R": R,
                                                "point_list": {},
                                                "index": 0,
                                                "target_LLA": target_LLA}
        pass

    def __handle_circle(self, attacker_ID, target_LLA, R):
        # 处理一下。
        point_list = self.abstract_state[attacker_ID]["point_list"]
        R = self.abstract_state[attacker_ID]["R"]
        index = self.abstract_state[attacker_ID]["index"]


        geshu = 6
        if len(point_list) == 0:
            # 重新生成一个点列
            point_list = self.__get_LLA_around(target_LLA, n_R=1, n_theta=geshu, dR=R)
            self.abstract_state[attacker_ID]["point_list"] = point_list
            index = 0
        else:
            attacker_LLA = self.__get_LLA(attacker_ID)
            point_next = point_list[index]
            jvli = self.distance(point_next[0], point_next[1], attacker_LLA[2],
                                 attacker_LLA[0], attacker_LLA[1], attacker_LLA[2])
            point_next2 = np.array([point_next[0], point_next[1]])
            attacker_LLA2 = np.array([attacker_LLA[0], attacker_LLA[1]])
            vector = point_next2-attacker_LLA2
            jvli = np.linalg.norm(vector)
            # if jvli<0.8*R/180*3.14*6371000:
            if jvli < 0.08*R:
                # 到了
                index = index + 1
                if index >= geshu:
                    index = 0

                # 这里如果是move_and_attack，就得把它结束掉。
        self.abstract_state[attacker_ID]["index"] = index
        point_next = point_list[index]
        self._Move_Action(attacker_ID, point_next[0], point_next[1], point_next[2])



    def __handle_move_and_attack(self, attacker_ID, target_LLA):
        # 这个应该要实现一个单位搜索前进，如果射程在范围里，就用合适的武器打一炮，但是不影响该走走。
        # 走到“指定位置在射程内了”，就往那里开一炮。
        # 还得整个东西闭环一下，是不是走到了。这个还挺关键的。
        # 搜索攻击应该是个状态，需要维持的那种。

        # 检测一下有没有合适的目标。
        # flag_attack = False  # 调试，先别开打炮
        flag_attack = True  # 调试，开始打炮了。

        if flag_attack:
            # detected_state_single = self.__detected_state_single(attacker_ID) # 应该从大池子来，不应该只看自己的观通。
            target_ID_local, target_LLA_local, target_distance_local = self.range_estimate(attacker_ID,
                                                                                           self.detected_state)  # 这里返回一个本步能够打到的目标
            if len(target_ID_local) > 0:
                # 说明找到能打的目标了，那就选个武器开始打了。
                weapon_selected = self.__weapon_select(attacker_ID, target_ID_local)

                if len(weapon_selected) > 0:
                    if (self.check_effect(target_ID_local, weapon_selected)):
                        # 如果有合适的武器，再考虑计算修正目标打提前量
                        target_LLA_local_modified = \
                            self.__target_LLA_local_modification(target_ID_local, target_LLA_local,
                                                                 target_distance_local
                                                                 , attacker_ID, weapon_selected)

                        # 然后到这里终于可以发出攻击指令了。
                        flag_zhimiao = self.check_zhimiao(attacker_ID, target_ID_local, weapon_selected)
                        if flag_zhimiao:  # 根据策略，武器类型和直瞄间瞄是不是匹配。如果判出来彳亍就打
                            self._Attack_Action(attacker_ID, target_LLA_local_modified[0], target_LLA_local_modified[1],
                                                target_LLA_local_modified[2], weapon_selected)
        else:
            print("XXHtest: attack disabled in __handle_move_and_attack")

        # 然后该打的打完了，就继续move呗
        attacker_LLA = self.__get_LLA(attacker_ID)
        jvli = self.distance(target_LLA[0], target_LLA[1], target_LLA[2],
                             attacker_LLA[0], attacker_LLA[1], attacker_LLA[2])  # 这里alt两个用成一样的，防止最后结束不了。

        if jvli > 10:
            # 那就是还没到，那就继续移动
            if self.abstract_state[attacker_ID]["flag_moving"] == False:
                # 那就是没动起来，那就得让它动起来。
                self._Move_Action(attacker_ID, target_LLA[0], target_LLA[1], target_LLA[2])
                self.abstract_state[attacker_ID]["flag_moving"] = True

            # 增加一个逻辑,处理万一车被打坏了动不了的情况.直接进隐蔽且改标志位.
            # 过滤一下，不然会导致跟随到一半的时候停了 # 还是别过滤了
            # if (self.abstract_state[attacker_ID]["jvli"] == jvli) and not ("next" in self.abstract_state[attacker_ID]):
            if (self.abstract_state[attacker_ID]["jvli"] == jvli):
                # 这一帧没动,不妙了.
                # self.set_hidden_and_alert(attacker_ID)
                self.__finish_abstract_state(attacker_ID)
                # self.abstract_state[attacker_ID]["flag_shelter"] = True # 反正动不了,就地隐蔽好了.
            else:
                self.abstract_state[attacker_ID]["jvli"] = jvli
        else:
            # 那就是到了，那就要改抽象状态里面了。
            self.__finish_abstract_state(attacker_ID)

    def __handle_move_and_attack2(self, attacker_ID, target_LLA):
        # 这个是改进开火的。
        flag_attack = True  # 调试，开始打炮了。

        if flag_attack:
            flag_done = self.__handle_one_shot_attack(attacker_ID)
        else:
            print("XXHtest: attack disabled in __handle_move_and_attack")

        # 然后该打的打完了，就继续move呗
        attacker_LLA = self.__get_LLA(attacker_ID)
        jvli = self.distance(target_LLA[0], target_LLA[1], target_LLA[2],
                             attacker_LLA[0], attacker_LLA[1], attacker_LLA[2])  # 这里alt两个用成一样的，防止最后结束不了。
        if jvli > 10:
            # 那就是还没到，那就继续移动
            if self.abstract_state[attacker_ID]["flag_moving"] == False:
                # 那就是没动起来，那就得让它动起来。
                self._Move_Action(attacker_ID, target_LLA[0], target_LLA[1], target_LLA[2])
                self.abstract_state[attacker_ID]["flag_moving"] = True
            if (self.abstract_state[attacker_ID]["jvli"] == jvli) and (self.num>100):
                self.__finish_abstract_state(attacker_ID)
            else:
                self.abstract_state[attacker_ID]["jvli"] = jvli
        else:
            # 那就是到了，那就要改抽象状态里面了。
            self.__finish_abstract_state(attacker_ID)

    def __handle_one_shot_attack(self, attacker_ID):
        # 整理一下，这段提出来。
        # 后面也可以加个标志位，让它能选择是不是自动开火。
        target_ID_local_list, target_LLA_local_list, target_distance_local_list \
            = self.range_estimate3(attacker_ID, self.detected_state)
        # list 里面是根据优先级排列的，优先级高的在前面。
        flag_done = False  # 这个量用来记录是不是打了一发了。
        if len(target_ID_local_list) > 0:
            for i in range(len(target_ID_local_list)):
                target_ID_local = target_ID_local_list[i]
                target_LLA_local = target_LLA_local_list[i]
                target_distance_local = target_distance_local_list[i]
                # 说明找到能打的目标了，那就选个武器开始打了。
                weapon_selected = self.__weapon_select(attacker_ID, target_ID_local)
                if len(weapon_selected) > 0:
                    if (self.check_effect(target_ID_local, weapon_selected)):
                        # 如果有合适的武器，再考虑计算修正目标打提前量
                        target_LLA_local_modified = \
                            self.__target_LLA_local_modification(target_ID_local, target_LLA_local,
                                                                 target_distance_local
                                                                 , attacker_ID, weapon_selected)
                        # 然后到这里终于可以发出攻击指令了。
                        # 有些武器直瞄好，有些武器间瞄好。# 有些武器只允许直瞄
                        flag_done = self.check_zhimiao(attacker_ID, target_ID_local, weapon_selected)
                        if flag_done:  # 根据策略，武器类型和直瞄间瞄是不是匹配。如果判出来彳亍就打
                            self._Attack_Action(attacker_ID, target_LLA_local_modified[0], target_LLA_local_modified[1],
                                                target_LLA_local_modified[2], weapon_selected)
                            break  # 打出来了，那就完事了
                else:
                    self._Change_State(attacker_ID, "hidden")
                    self.abstract_state[attacker_ID]["flag_shelter"] = True
        else:
            pass
        return flag_done

    def __handle_hidden_and_alert(self, attacker_ID, GetLandForm=0):
        # 在这里集成一个“寻找周围安全区域”的逻辑

        # 卫星、飞机和bmc3是不吃这个指令的，还是区分一下以防后面报错在
        flag = ("bmc" in attacker_ID) or ("HEO_infrared_satallite" in attacker_ID) or (
                "ShipboardCombat_plane" in attacker_ID)
        if flag:
            return

        # print("XXHtest: __handle_hidden_and_alert disabled for debug")
        # return

        # 还可以优化。没必要每一步都求一次，只需求随便求几次，收敛了就罢了。
        if self.abstract_state[attacker_ID]["flag_shelter"] == False:
            LLA_here = self.__get_LLA(attacker_ID)
            LLA_shelter, shelter_flag = self.__get_shelter(LLA_here, GetLandForm)
            if shelter_flag:
                # 到了，隐蔽起来了，就把参数改了，然后隐蔽起来
                self.abstract_state[attacker_ID]["flag_shelter"] = True
                self._Change_State(attacker_ID, "hidden")
            else:
                # 还没到，那就移动过去。
                # 本来应该是移动攻击过去，但是防止抽象命令互相调用，直接挪过去好了。
                self._Move_Action(attacker_ID, LLA_shelter[0], LLA_shelter[1], LLA_shelter[2])

        # 然后，如果攻击范围里有敌人，就找个合适的打。这段跟搜索攻击里面攻击那段是一样的。
        flag_done = self.__handle_one_shot_attack(attacker_ID)

        return
        # print("XXHtest: unfinished yet, __handle_hidden_and_alert")
        # pass

    def __handle_partrol_and_monitor(self, attacker_ID, target_LLA):
        # 这个是真的开始实现了.# 整点随机性，在一系列点比如圆周之间反复横跳，如果看到敌人，就反方向跑路
        jvli_threshold = 500
        # 如果没到目标区域，那就赶紧往那边去，尽量要复用
        if self.abstract_state[attacker_ID]["flag_arrived"] == False:
            # 到了再产点
            attacker_LLA = self.__get_LLA(attacker_ID)
            jvli = self.distance(attacker_LLA[0], attacker_LLA[1], 0, target_LLA[0], target_LLA[1], 0)
            if jvli > jvli_threshold:
                # 说明还没到呢，得设定一个过去的抽象状态。
                next = self.abstract_state[attacker_ID]
                # 强行实现了一个堆栈调用那种意思，笨点但是有用。然后改成move的抽象状态
                self.set_move_and_attack(attacker_ID, target_LLA)
                self.abstract_state[attacker_ID]["next"] = next  # 然后把它放回去，准备跑完了之后看
            else:
                # 说明到了，要开始搞随机点防止被爆了。
                self.abstract_state[attacker_ID]["flag_arrived"] = True

        else:
            # 如果一开始就是到了的，走这个分支
            # 然后看探测池子里面敌人的距离。
            target_ID_local, target_LLA_local, target_distance_local \
                = self.range_estimate2(attacker_ID, self.detected_state)

            flag = (target_distance_local < jvli_threshold) and (
                        not ("truck" in attacker_ID) or ("Infantry" in attacker_ID))
            if flag:
                # 距离太近就要润了。按说得区分不同的目标的逃跑距离，但是先不慌写。
                # 算个target_new出来
                target_LLA = np.array(target_LLA)  # 原来的目标点
                target_LLA_local = np.array(target_LLA_local)  # 那附近有敌人
                vector_LLA = target_LLA_local - target_LLA

                # 重新设定target，润过去
                target_LLA_new = target_LLA + (-1) * vector_LLA * 2  # 跑路常数，表征跑多远，按说不应该硬编码
                self.abstract_state[attacker_ID]["target_LLA"] = target_LLA_new
                self.abstract_state[attacker_ID]["flag_arrived"] = False  # 改了之后标志位也得改。

                next = self.abstract_state[attacker_ID]
                self.set_move_and_attack(attacker_ID, target_LLA)
                self.abstract_state[attacker_ID]["next"] = next  # 然后把它放回去，准备跑完了之后看
            else:
                # 意思需要生成周边的点。比如300米左右半径的范围内
                if ("truck" in attacker_ID) or ("Infantry" in attacker_ID):
                    LLA_around_list = self.__get_LLA_around(target_LLA, n_R=1, n_theta=1, dR=0.0005)
                else:
                    LLA_around_list = self.__get_LLA_around(target_LLA, n_R=1, n_theta=1, dR=0.003)
                self.abstract_state[attacker_ID]["flag_arrived"] = True  # 改了之后标志位也得改。
                next = self.abstract_state[attacker_ID]
                self.set_move_and_attack(attacker_ID, LLA_around_list[0])  # 不改标志位，往随机点去
                self.abstract_state[attacker_ID]["next"] = next
                # 没有距离太近的就看有没有到了选定的move过去的随机点。

        # print("XXHtest: unfinished yet, __handle_partrol_and_monitor")
        # 这个状态也是可以长期持续的，所以不需要退出条件。
        pass

    def __handle_open_fire(self, attacker_ID):
        # 寻找目标,对范围内最近的目标火力全开
        # 还是存在那个问题,选目标是按照距离而不是按照武器选的,所以可能会出现无效的攻击命令.
        target_ID_local, target_LLA_local, target_distance_local = self.range_estimate(attacker_ID,
                                                                                       self.detected_state)  # 这里返回一个本步能够打到的目标
        if len(target_ID_local) > 0:
            target_LLA_local = target_LLA_local
        else:
            # 没探索到，那就直接盲打，默认LLA
            target_LLA_local = self.abstract_state[attacker_ID]["target_LLA"]
            target_ID_local = "void"

        attack_num = 0
        # 说明找到能打的目标了，那就选个武器开始打了。
        WeaponState_list = self.status[attacker_ID]["WeaponState"]
        for weapon_selected in WeaponState_list:
            if (weapon_selected["WeaponCD"] == 0) and (weapon_selected["WeaponNum"] > 0):
                flag_effect = self.check_effect(target_ID_local, weapon_selected)
                if flag_effect:
                    # 那就是可以打,就直接打了
                    target_LLA_local_modified = \
                        self.__target_LLA_local_modification(target_ID_local, target_LLA_local, target_distance_local
                                                             , attacker_ID, weapon_selected)
                    # 然后到这里终于可以发出攻击指令了。
                    self._Change_State(attacker_ID, "hidden")
                    self._Attack_Action(attacker_ID, target_LLA_local_modified[0], target_LLA_local_modified[1],
                                        target_LLA_local_modified[2], weapon_selected["WeaponType"][0:-9])
                    attack_num = attack_num + 1

        # 直接return
        # print("XXHtest: unfinished yet, __handle_open_fire")
        # pass
        # if attack_num == 0 :
        # 说明是找到目标了,而且所有武器试了一遍都没有打出去.
        # 这个不退出了，还不如一直等CD
        # self.__finish_abstract_state(attacker_ID)
        return

    def __handle_open_fire2(self, attacker_ID):
        WeaponState_list = self.status[attacker_ID]["WeaponState"]
        geshu = len(WeaponState_list)
        for i in range(geshu):
            self.__handle_one_shot_attack(attacker_ID)

    def __handle_none(self, attacker_ID):
        # 说是none，就是none。不发任何命令，就纯纯的空跑。
        pass

    def __handle_follow_and_defend(self, attacker_ID, VIP_ID, flag_stand_by):
        # 思路是，把VIP周围的随机位置定为目标，然后A过去。flag_stand_by标记是不是到位且没敌人了
        # 如果VIP周围有目标，距离要是近了，那就A股过去。防御场景下可实现简单的步炮协同。
        # 如果自己位置距离VIP的位置远了，那就更改一次位置。
        # 如果距离不远，那就藏好。谁过来就A它。
        # 如果VIP寄了，那也是藏好。

        # 首先自然是把自己和VIP的位置搞出来。
        VIP_LLA = self.__get_LLA(VIP_ID)
        attacker_LLA = self.__get_LLA(attacker_ID)

        # 不对，应该是有敌人先打敌人。没有，再调整战术位置。
        # 调整战术位置的部分完事了，然后就开始写保卫逻辑了。就整个简单的，探测到的距离近的就A过去。
        target_ID_local, target_LLA_local, target_distance_local \
            = self.range_estimate2(VIP_ID, self.detected_state)

        if target_distance_local < 2000:  # 预想的VIP是炮或者导弹车，而能打他们的东西射程都不近，所以要勇于冲锋
            # 这意思敌人进了危险距离了，得给它冲了
            self.abstract_state[attacker_ID]["flag_stand_by"] = False  # 动了，所以隐蔽状态没了。
            next = self.abstract_state[attacker_ID]
            self.set_move_and_attack(attacker_ID, target_LLA_local)
            self.abstract_state[attacker_ID]["next"] = next  # 然后把它放回去，准备跑完了之后看
        else:
            # 没敌人，调整战术位置，A到VIP周围去。
            # 距离判断，是否需要动。
            VIP_distance = self.distance(VIP_LLA[0], VIP_LLA[1], VIP_LLA[2], attacker_LLA[0], attacker_LLA[1],
                                         attacker_LLA[2])

            if VIP_distance > 50:  # 只要不会被AOE波及就好了，然后尽量离得近一点。
                # 大于说明不得行，得重新调整位置。留点误差，防止变成一致A来A去。
                self.abstract_state[attacker_ID]["flag_stand_by"] = False
                attacker_LLA_new = self.__get_LLA_around(VIP_LLA, n_R=1, n_theta=1, dR=0.0004)
                # 取出坐标之后A过去。得设定一个过去的抽象状态。
                next = copy.deepcopy(self.abstract_state[attacker_ID])
                self.set_move_and_attack(attacker_ID, attacker_LLA_new[0])
                self.abstract_state[attacker_ID]["next"] = next  # 然后把它放回去，准备跑完了之后看
            else:
                # 说明距离是合适的。那就就地隐蔽好了,因为要防御所以战术位置是关键的，不再找隐藏点了。
                # 抽象状态能不嵌套还是别嵌套，使用标志位flag_stand_by
                if flag_stand_by == False:
                    # 说明还没有到位隐蔽，那就隐蔽然后改标志位。
                    self._Change_State(attacker_ID, "hidden")
                    self.abstract_state[attacker_ID]["flag_stand_by"] = True
        # 这个抽象状态也是可以长期保持的，因此不需要额外设定完成退出的检测。

    def __handle_charge_and_xiache(self, attacker_ID, infantry_ID, target_LLA, flag_state):
        # 没在车上就过去接，在车上就A过去，到地方就下车隐蔽，有敌人就下车A它
        # 记录一些状态，没上车且不能上1。没上车且正在上2。在车上且没敌人就3。在车上且有敌人就4。下去打完理论上就1了。
        # 不行，还得再简化，取消中间下车打的说法，就是A过去才下车所以在车上不判断是不是遇到敌人了，就突出一个头铁。一条就是一条。别太嵌套。
        attacker_LLA = self.__get_LLA(attacker_ID)
        try:
            infantry_LLA = self.__get_LLA(infantry_ID)
        except:
            # 这个就是步兵不在态势里了。
            infantry_LLA = [0, 0, 0]

        jvli = self.distance(attacker_LLA[0], attacker_LLA[1], attacker_LLA[2],
                             infantry_LLA[0], infantry_LLA[1], attacker_LLA[2])

        if flag_state == 1:
            # 没上车且距离远，那就得过去。
            if jvli < 100:
                # 那就是到了，转变为可以上车的状态。
                flag_state = 2
                self.abstract_state[attacker_ID]["flag_state"] = flag_state
            elif jvli < 30000:
                # 距离不够，那就过去接。简化逻辑，只写一个过去接，不假设过程中会动或者什么的。
                abstract_state_next = copy.deepcopy(self.abstract_state[attacker_ID])
                self.set_move_and_attack(attacker_ID, infantry_LLA)
                self.abstract_state[attacker_ID]["next"] = abstract_state_next  # 然后把它放回去，准备跑完了之后再复原。
            else:
                # 那就是步兵已经寄了，那就直接退化成move and attack就完事儿了。
                self.set_move_and_attack(attacker_ID, target_LLA)
                # 不写next堆栈了，所以在set_move_and_attack里面直接finish就完事了。
        if flag_state == 2:
            # 没上车且正在上,或者说条件姑且具备了。
            if self.abstract_state[attacker_ID]["num_wait"] > 0:
                # 那就是等着呢，那就等会儿好了。
                self.abstract_state[attacker_ID]["num_wait"] = self.abstract_state[attacker_ID]["num_wait"] - 1
                pass
            else:
                if jvli < 100:
                    # 那就是到了，那就上车。
                    self._Change_State(attacker_ID, "stay")
                    self._Change_State(infantry_ID, "stay")
                    self._On_Board_Action(attacker_ID, infantry_ID)
                    self.abstract_state[attacker_ID]["num_wait"] = 5
                elif jvli <= 30000:
                    # 那就是没到且可以去。
                    flag_state = 1
                    self.abstract_state[attacker_ID]["flag_state"] = flag_state
                elif jvli > 30000:
                    # 那就是对应的步兵已经没了，上车完成或者是真的没了。转换一下。
                    flag_state = 3
                    self.abstract_state[attacker_ID]["flag_state"] = flag_state
            pass
        if flag_state == 3:
            # 开冲。 如果到了就放下来分散隐蔽，兵力分散火力集中。
            # 不要再闭环到1了，这样防止这东西死循环。
            if self.abstract_state[attacker_ID]["num_wait"] > 0:
                # 那就是等着呢，那就等会儿好了。
                self.abstract_state[attacker_ID]["num_wait"] = self.abstract_state[attacker_ID]["num_wait"] - 1
                pass
            else:
                # 进堆栈，A过去。
                abstract_state_next = copy.deepcopy(self.abstract_state[attacker_ID])
                self.set_move_and_attack(attacker_ID, target_LLA)
                self.abstract_state[attacker_ID]["next"] = abstract_state_next  # 然后把它放回去，准备跑完了之后再复原。

                jvli2 = self.distance(attacker_LLA[0], attacker_LLA[1], attacker_LLA[2],
                                      target_LLA[0], target_LLA[1], attacker_LLA[2])
                if jvli2 < 100:
                    # 那就算是到了，没必要搞出奇怪的东西
                    # 到了就下车隐蔽
                    self._Change_State(attacker_ID, "stay")
                    # self._Change_State(infantry_ID, "stay")
                    self._Off_Board_Action(attacker_ID, infantry_ID)
                    self.abstract_state[attacker_ID]["num_wait"] = 5
                    pass
                    if jvli < 20000:
                        # 说明步兵ID已经有了，那就是下车成功了或者无论如何，反正步兵在地上。
                        # 而且没有敌人，先结束，原地藏起来。原地藏起来隐含了有敌人就A过去，所以不用单独写有敌人就A过去了。
                        # 这么写的话就可以中途搞几次下车警戒之类的，也没啥不好的。
                        self.__finish_abstract_state(attacker_ID)
                        self.__finish_abstract_state(attacker_ID)
                        # 这里存在一个问题，下车完成之后车本身是move_and_attack,而charge_and_xiache在抽象状态里面，所以要结束两次

                        # self.__finish_abstract_state(infantry_ID) # Python不让我直接这么玩。彳亍口巴
                    else:
                        # 那就是没步兵了反正。
                        # self.__finish_abstract_state(attacker_ID)
                        # self.__finish_abstract_state(attacker_ID)
                        pass
            pass

        # print("unfinished yet, __handle_charge_and_xiache")

    def __finish_abstract_state(self, attacker_ID):
        # 统一写一个完了之后清空的，因为也不完全是清空，还得操作一些办法。
        # 暴力堆栈了其实是，笨是笨点但是有用。

        if attacker_ID in self.abstract_state:
            pass
        else:
            # 这个是用来处理步兵上下车逻辑的。上车之后删了，下车之后得出来
            self.abstract_state[attacker_ID] = {}  # 统一取成空的，后面再统一变成能用的。

        if "next" in self.abstract_state[attacker_ID]:
            next_abstract_state = self.abstract_state[attacker_ID]['next']
        else:
            next_abstract_state = {}
        self.abstract_state[attacker_ID] = next_abstract_state

    def __weapon_select(self, attacker_ID, target_ID):
        # 这里整一个“根据敌我情况选择合适的武器”的东西，应该会被多次调用。
        # target_ID 如果没有，就打一炮比较便宜的。
        # 这种是一秒完成的，就不需要闭环了。
        WeaponState_list = self.status[attacker_ID]["WeaponState"]
        selected_weapon = ""
        for i in range(len(self.weapon_list)):
            # 优先级从上到下，如果有这个武器，就再判断能不能打。能打就直接退了。
            # 有问题，能打且CD哪些都是合适的才行。
            # 存在逻辑漏洞，不同优先级的武器射程未必单调递减，但是鉴定为影响不大先这样吧。xxh1007
            candidate_weapon = self.weapon_list[i]
            if self.__weapon_check(candidate_weapon, WeaponState_list):
                selected_weapon = candidate_weapon
                break
        return selected_weapon

    def __weapon_check(self, candidate_weapon, WeaponState_list):
        # 判断WeaponList里面有没有这个ID。不是dic所以不能直接“in”

        geshu = len(WeaponState_list)
        flag = False

        for i in range(geshu):
            if candidate_weapon in WeaponState_list[i]["WeaponID"]:

                if "HighExplosiveShot" in candidate_weapon and self.num < 1500:
                    geshu = 5
                else:
                    geshu = 0

                if (WeaponState_list[i]["WeaponCD"] == 0) and (WeaponState_list[i]["WeaponNum"] > geshu):
                    # 说明这个弹还有，CD也还合适，鉴定为能打
                    flag = True

        return flag

    def range_estimate(self, attacker_ID, detectinfo):
        # 这个是寻找范围内是否有它打得到的。
        # 可以整点儿活儿，比如不要极限射程开火。

        # detectinfo = self.get_detect_info(status) # 没必要每个里面都get一遍

        # 先搞一点默认值
        enemy_ID_selected = ""
        enemy_distance_min = 1145141919810
        bili = 0.9  # 不要极限距离开火的超参数
        enemy_LLA_selected = [0, 0, 0]

        flag_fangan = 2
        if flag_fangan == 1:
            # 方案1，就无脑来最简单的
            for enemy_ID in detectinfo:
                # 检测是不是合适打。
                attacker_LLA = self.__get_LLA(attacker_ID)
                target_LLA = [detectinfo[enemy_ID]["targetLon"], detectinfo[enemy_ID]["targetLat"], attacker_LLA[2]]
                enemy_distance = self.distance(target_LLA[0], target_LLA[1], target_LLA[2],
                                               attacker_LLA[0], attacker_LLA[1], attacker_LLA[2])
                flag_select = False  # 整个flag变量比直接全用if else能够少几行
                if enemy_distance < enemy_distance_min:
                    flag_select = ((("MainBattleTank" in attacker_ID) or ("Howitzer_C100" in attacker_ID)) and (
                            enemy_distance < 2500 * bili)) \
                                  or ((("ArmoredTruck" in attacker_ID) or ("WheeledCmobatTruck" in attacker_ID)) and (
                            enemy_distance < 700 * bili)) \
                                  or ((("Infantry" in attacker_ID)) and (enemy_distance < 400 * bili)) \
                                  or (("missile_truck" in attacker_ID) and (enemy_distance < 600000 * bili)) \
                                  or (("ShipboardCombat_plane" in attacker_ID) and (enemy_distance < 15000 * bili))

                if flag_select:
                    enemy_distance_min = enemy_distance  # 反正只需要取一个最近的，就不用保存了。
                    enemy_ID_selected = enemy_ID
                    enemy_LLA_selected = target_LLA
        elif flag_fangan == 2:
            # 方案2，尝试加入优先级。
            # 方案2改，这个是改了发现概率之后。恐怕目标ID还不能只从当前帧的位置来，因为现在detectinfo里面的变量是若有若无的。
            # 方案2改2，这个是增加了子弹不打车的，或者说无效的就不打。
            prior_list = self.get_prior_list(attacker_ID)
            for i in range(len(prior_list)):
                prior_str = prior_list[i]  # 其实就是根据优先级多做几次方案1，而已。
                flag_select_prior = False
                # for enemy_ID in detectinfo:
                for enemy_ID in self.detected_state2:
                    # 检测这个目标是不是新鲜的。
                    if self.detected_state2[enemy_ID]["this"]["num"] < self.num - 5:
                        # 就说明目标信息已经不新鲜了，就不打了 # 正常情况下，这里面有的肯定都有this属性
                        # 如果这帧是能够detectinfo里有的，那肯定已经更新到deteced_state2里面了。
                        continue

                    # 如果目标是新鲜的，就检测是不是合适打。
                    attacker_LLA = self.__get_LLA(attacker_ID)
                    # target_LLA = [detectinfo[enemy_ID]["targetLon"], detectinfo[enemy_ID]["targetLat"], attacker_LLA[2]]
                    target_LLA = self.detected_state2[enemy_ID]["this"]["LLA"]
                    enemy_distance = self.distance(target_LLA[0], target_LLA[1], target_LLA[2],
                                                   attacker_LLA[0], attacker_LLA[1], attacker_LLA[2])
                    flag_select = False
                    if (enemy_distance < enemy_distance_min) and (prior_str in enemy_ID):
                        flag_select = (("MainBattleTank" in attacker_ID) and (enemy_distance < 2500 * bili)) \
                                      or (("Howitzer_C100" in attacker_ID) and (enemy_distance < 7000 * bili)) \
                                      or (("ArmoredTruck" in attacker_ID) and (enemy_distance < 1000 * bili)) \
                                      or (("WheeledCmobatTruck" in attacker_ID) and (enemy_distance < 700 * bili)) \
                                      or (("Infantry" in attacker_ID) and (enemy_distance < 1000 * bili)) \
                                      or (("missile_truck" in attacker_ID) and (enemy_distance < 600000 * bili)) \
                                      or (("ShipboardCombat_plane" in attacker_ID) and (enemy_distance < 15000 * bili))
                    if flag_select:
                        enemy_distance_min = enemy_distance  # 反正只需要取一个优先级最高的，也不用存。
                        # 确切地说，同一优先级里最近的
                        enemy_ID_selected = enemy_ID
                        enemy_LLA_selected = target_LLA
                        flag_select_prior = True  # 如果选到至少一个了，就说明不用再寻找下一个优先级的了。
                if flag_select_prior:
                    # 这个优先级里面如果选到合适的了，就不用再循环了，就可以退出去了。
                    break
        elif flag_fangan == 3:
            print("not finished yet")
            pass

        return enemy_ID_selected, enemy_LLA_selected, enemy_distance_min

    def range_estimate_gai(self, attacker_ID, detectinfo):
        # 这个是寻找范围内是否有它打得到的。range_estimate的升级版
        # 这个是基于range_estimate3的那个逻辑的。detectinfo只是用来保持一致性的。
        target_ID_local_list, target_LLA_local_list, target_distance_local_list \
            = self.range_estimate3(attacker_ID, self.detected_state)
        prior_list = self.get_prior_list(attacker_ID)
        enemy_ID_selected = ""
        enemy_LLA_selected = ""
        enemy_distance_min = ""
        for i in range(len(prior_list)):
            for j in range(len(target_ID_local_list)):
                if prior_list[i] in target_ID_local_list[j]:
                    # 那就是根据优先级从探测池子里面找到了值得A过去的东西了。
                    # 这个和开火完全可以用一个逻辑啊
                    enemy_ID_selected = target_ID_local_list[j]
                    enemy_LLA_selected = target_LLA_local_list[j]
                    enemy_distance_min = target_distance_local_list[j]

        return enemy_ID_selected, enemy_LLA_selected, enemy_distance_min

    def range_estimate3(self, attacker_ID, detectinfo):
        # 这个是寻找所有打得到的，以列表的形式给出
        enemy_ID_selected_list = []
        enemy_LLA_selected_list = []
        enemy_distance_min_list = []

        # 先搞一点默认值
        enemy_ID_selected = ""
        enemy_distance_min = 1145141919810
        bili = 0.95  # 不要极限距离开火的超参数
        enemy_LLA_selected = [0, 0, 0]

        # 方案2，尝试加入优先级。
        # 方案2改，这个是改了发现概率之后。恐怕目标ID还不能只从当前帧的位置来，因为现在detectinfo里面的变量是若有若无的。
        # 方案2改2，这个是增加了子弹不打车的，或者说无效的就不打。
        prior_list = self.get_prior_list(attacker_ID)
        for i in range(len(prior_list)):
            prior_str = prior_list[i]  # 其实就是根据优先级多做几次方案1，而已。
            flag_select_prior = False
            # for enemy_ID in detectinfo:
            for enemy_ID in self.detected_state2:
                # 检测这个目标是不是新鲜的。
                if self.detected_state2[enemy_ID]["this"]["num"] < self.num - 5:
                    # 就说明目标信息已经不新鲜了，就不打了 # 正常情况下，这里面有的肯定都有this属性
                    # 如果这帧是能够detectinfo里有的，那肯定已经更新到deteced_state2里面了。
                    continue

                # 如果目标是新鲜的，就检测是不是合适打。
                attacker_LLA = self.__get_LLA(attacker_ID)
                target_LLA = self.detected_state2[enemy_ID]["this"]["LLA"]
                enemy_distance = self.distance(target_LLA[0], target_LLA[1], target_LLA[2],
                                               attacker_LLA[0], attacker_LLA[1], attacker_LLA[2])
                flag_select = False
                # 在当前逻辑下，只要找最大范围内的就行了。
                if (enemy_distance < enemy_distance_min) and (prior_str in enemy_ID):
                    flag_select = (("MainBattleTank" in attacker_ID) and (enemy_distance < 2500 * bili)) \
                                  or (("Howitzer_C100" in attacker_ID) and (enemy_distance < 7000 * bili)) \
                                  or (("ArmoredTruck" in attacker_ID) and (enemy_distance < 1000 * bili)) \
                                  or (("WheeledCmobatTruck" in attacker_ID) and (enemy_distance < 700 * bili)) \
                                  or (("Infantry" in attacker_ID) and (enemy_distance < 800 * bili)) \
                                  or (("missile_truck" in attacker_ID) and (enemy_distance < 600000 * bili)) \
                                  or (("ShipboardCombat_plane" in attacker_ID) and (enemy_distance < 5000 * bili))
                    # or (("ShipboardCombat_plane" in attacker_ID) and (enemy_distance < 15000 * bili))
                if flag_select:
                    enemy_distance_min_list.append(enemy_distance)
                    enemy_ID_selected_list.append(enemy_ID)
                    enemy_LLA_selected_list.append(target_LLA)

            # # 算了一步到位直接，有几个要几个。
            # if len(enemy_ID_selected_list)>=5:
            #     # 找五个选一个很给面子了，还想咋样嘛。
            #     break

        return enemy_ID_selected_list, enemy_LLA_selected_list, enemy_distance_min_list

    def range_estimate2(self, attacker_ID, detectinfo):
        # 区分一下，这个是不考虑任何武器射程的，找个最近的。
        enemy_ID_selected = ""
        enemy_distance_min = 114514
        enemy_distance = 1919810
        bili = 0.99  # 不要极限距离开火的超参数
        enemy_LLA_selected = [0, 0, 0]

        for enemy_ID in detectinfo:
            # 检测是不是合适打。
            attacker_LLA = self.__get_LLA(attacker_ID)
            target_LLA = [detectinfo[enemy_ID]["targetLon"], detectinfo[enemy_ID]["targetLat"], attacker_LLA[2]]
            enemy_distance = self.distance(target_LLA[0], target_LLA[1], target_LLA[2],
                                           attacker_LLA[0], attacker_LLA[1], attacker_LLA[2])

            if enemy_distance < enemy_distance_min:
                enemy_distance_min = enemy_distance  # 反正只需要取一个最近的，就不用保存了。
                enemy_ID_selected = enemy_ID
                enemy_LLA_selected = target_LLA

        return enemy_ID_selected, enemy_LLA_selected, enemy_distance_min

    def __target_LLA_local_modification(self, target_ID_local, target_LLA_local,
                                        target_distance_local, attacker_ID, weapon_selected):
        # 这里按说得有什么轨迹预测之类的东西(target_ID_local, target_LLA_local,target_distance_local
        #                                                              ,attacker_ID,weapon_selected)

        # return target_LLA_local # 测试用的，提前量关了打一把看看。

        # 有些东西是不预测的，不然全烂完了。
        filter_list = ["Short", "Ship"]
        for filter_str in filter_list:
            if filter_str in target_ID_local:
                return target_LLA_local
        if "Short" in weapon_selected or "RPG" in weapon_selected:
            return target_LLA_local

        # 增加一版专业的加减乘除一下的，
        V_dan = self.weapon_V[weapon_selected]
        # attacker_LLA = self.__get_LLA(attacker_ID)
        # L_dan = self.distance(target_LLA_local[0], target_LLA_local[1], target_LLA_local[2],
        #                       attacker_LLA[0], attacker_LLA[1], attacker_LLA[2])
        L_dan = target_distance_local
        t_dan = int(L_dan / V_dan)

        flag_fangan = 2
        if flag_fangan == 1:
            # 方案1，直接用探测池子里面的东西做预测。用这个的话其实不用输入target_LLA_local也能做，但是算了，和以前的保持统一。
            lon_last = self.detected_state[target_ID_local]["targetLastLon"]
            lat_last = self.detected_state[target_ID_local]["targetLastLat"]
            alt_last = self.detected_state[target_ID_local]["targetLastAlt"]

            lon = self.detected_state[target_ID_local]["targetLon"]
            lat = self.detected_state[target_ID_local]["targetLat"]
            alt = self.detected_state[target_ID_local]["targetAlt"]

            if lon_last == -1:
                # 说明没有，那就算了。
                target_LLA_local_modified = target_LLA_local
            else:
                # 说明有两个点，那就可以搞起来了
                target_LLA_last = np.array([lon_last, lat_last, alt_last])
                target_LLA_this = np.array([lon, lat, alt])  # 这个就应该等于target_LLA_local

                # 然后插值嘛，最简单的插值就行了
                vector_move = target_LLA_this - target_LLA_last
                target_LLA_local_modified = target_LLA_this + vector_move * 1.2
                # 这个是考虑弹速的提前量。这么写粗糙归粗糙，但是实现起来就简单得非常多了，鉴定为好。
        elif flag_fangan == 2:
            # 方案2，用自己记录的那两帧来插值。复杂点，但是可以规避方案1的“只能动对动”的问题。
            # if len(self.detected_state2) == 0:
            #     print("self.detected_state2 disabled, thus __target_LLA_local_modification model 2 disabled")
            #     target_LLA_local_modified = target_LLA_local  # 不要在分支里面随便return，改改值是没问题的。

            if not (target_ID_local in self.detected_state2):
                target_LLA_local_modified = target_LLA_local
                # 处理一下空的，默认返回一个不变的，防止不必要的报错。
            else:
                if "last" in self.detected_state2[target_ID_local]:
                    target_LLA_last = self.detected_state2[target_ID_local]["last"]["LLA"]
                    num_last = self.detected_state2[target_ID_local]["last"]["num"]
                    target_LLA_this = self.detected_state2[target_ID_local]["this"]["LLA"]
                    num_this = self.detected_state2[target_ID_local]["this"]["num"]
                    # 然后开始计算了
                    vector_move = np.array(target_LLA_this) - np.array(target_LLA_last)
                    vector_move = vector_move / (num_this - num_last + 0.000001)
                    if target_distance_local < 800:
                        canshu = 0.9
                    # elif (target_distance_local > 800) and (target_distance_local < 1500):
                    #     canshu = 1
                    elif (target_distance_local > 1500) and (target_distance_local < 3000):
                        canshu = 2
                    elif (target_distance_local > 3000) and (target_distance_local < 7000):
                        canshu = 3
                    else:
                        canshu = 0  # 这个是给导弹的
                    # canshu = 3
                    if "Tank" in attacker_ID:
                        canshu = canshu + 1
                    if "ZTZ200" in attacker_ID:
                        canshu = canshu + 1
                    if "Truck" in target_ID_local:
                        canshu = canshu + 1
                    canshu = t_dan + canshu
                    target_LLA_local_modified = target_LLA_this + vector_move * canshu
                    # 也是稍微来点提前量。
                else:
                    # 没存到，这一帧刚进来的，那就直接打它。
                    # 按说这个是可以照着它写的。
                    target_LLA_local_modified = target_LLA_local
        elif flag_fangan == 0:
            # 开摆就完事儿了
            target_LLA_local_modified = target_LLA_local
        return target_LLA_local_modified

    def __get_LLA(self, ID):
        # 这个就是单纯的从status里面把LLA拿出来。
        try:
            lon = self.status[ID]["VehicleState"]["lon"]
            lat = self.status[ID]["VehicleState"]["lat"]
            alt = self.status[ID]["VehicleState"]["alt"]
        except:
            # 直接用异常处理吧，来处理万一单位炸了之后会发生什么。
            lon = 0
            lat = 0
            alt = 0

        LLA = [lon, lat, alt]

        return LLA

    def __get_LLA_around(self, LLA, n_R=3, n_theta=12, dR=0.0001):
        # 这个是用来随便取一堆周围的点
        LLA = np.array(LLA)
        # dR = 0.0001  # 对应大概11米
        theta0 = np.random.randint(0, 314 * 2) / 100  # 初始角度姑且是0到2pi来个随机的
        dtheta = 2 * np.pi / n_theta  # 三十度取一条射线，已经很给面子了。
        LLA_around_list = []
        for i in range(n_R):
            for j in range(n_theta):
                fangxiang = np.array([np.cos(theta0 + dtheta * j), np.sin(theta0 + dtheta * j), 0])
                LLA_single = LLA + dR * (i + 1) * fangxiang
                LLA_around_list.append(LLA_single)
        return LLA_around_list

    def __get_shelter(self, LLA_here, GetLandForm):
        # 这个“寻找周围安全区域，如果比现在的还安全，就准备过去”，返回坐标和标志位。

        # 摆了，随便返回一个什么就拉倒了。避免取地形了。
        LLA_here = LLA_here
        shelter_flag = True  # 直接原地认为是好的，完事儿了。
        return LLA_here, shelter_flag

        LLA_around_list = self.__get_LLA_around(LLA_here, n_R=3, n_theta=6, dR=0.001)

        dixing_dic = GetLandForm(LLA_here[0], LLA_here[1])
        dixing_dic = eval(dixing_dic)
        try:
            landform_here = dixing_dic["landform"]
        except:
            # 那就说明取地形这一步由于未知原因寄了,给整个默认的地形好了.
            landform_here = "default"

        shelter_flag = True

        # 然后遍历那一堆点，比较地形。按说应该写个枚举类，下次一定。
        geshu = len(LLA_around_list)
        for i in range(geshu):
            LLA_there = LLA_around_list[i]

            dixing_dic = GetLandForm(LLA_there[0], LLA_there[1])
            dixing_dic = eval(dixing_dic)
            landform_there = dixing_dic["landform"]

            if landform_type[landform_there].value < landform_type[landform_here].value:
                landform_here = landform_there
                LLA_here = LLA_there
                shelter_flag = False  # 还没到位，改标志位
        return LLA_here, shelter_flag

    def __detected_state_all(self):
        # 这里面维护一个本方探测到的所用东西，如果有东西的的话。
        # 就过一遍所有装备的探测池子，就行了。
        # 结果还是重复造轮子了。备保吧，说不定就用上了呢。
        detected_state_all = []
        for ID in self.status:
            detected_state_single = self.__detected_state_single(ID)
            # detected_state_all.append(detected_state_single)
            detected_state_all = detected_state_all + detected_state_single
        return detected_state_all
        # print("XXHtest: unfinished yet")

    def __detected_state_single(self, ID):
        # 这就是一个本方特定装备自己能探测到的池子.
        detected_state_single = []

        # 有些东西是会报错的，需要提前返回回去
        if 'bmc' in ID:
            return detected_state_single

        detector_state_single = self.status[ID]['DetectorState']

        if len(detector_state_single) > 0:
            for i in range(len(detector_state_single)):
                detected_state_single_tmp = detector_state_single[i]['DetectedState']
                # detected_state_single.append(detected_state_single_tmp)
                detected_state_single = detected_state_single + detected_state_single_tmp

        # # 后面这几行是开发过程中用的，正常是不开的。
        # if len(detected_state_single) > 0:
        #     print("XXHtest: unfinished yet")

        return detected_state_single

    def load_xlsx_deploy(self, xls_name=r'Deployment_ArmoredTruck_ZTL100'):
        # 这个是用来加载外部excel的，返回各种部署坐标。
        file_name = self.deploy_folder + "\\" + xls_name + ".xlsx"
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

    def get_state(self, cur_myState, cur_enemyState):
        # 把这些个东西整成能够检索的形式。以及比对是不是有东西被摧毁了
        self.my_state = cur_myState
        self.enemy_state = cur_enemyState
        pass

    def get_status(self):
        # 这个是新加的，用于接大模型
        return self.status , self.detected_state 

    def update_detectinfo(self, detectinfo):
        # 处理一下缓存的探测。
        # 好吧,这个并不需要。探测池子里面给到的“上一步”似乎是对的。
        for target_ID in detectinfo:
            for filter_ID in self.weapon_list:
                if filter_ID in target_ID:
                    continue  # 如果探测到的是弹药，那就不要了。

            target_state = {}

            target_state_single = {}
            lon = detectinfo[target_ID]["targetLon"]
            lat = detectinfo[target_ID]["targetLat"]
            alt = detectinfo[target_ID]["targetAlt"]
            LLA = [lon, lat, alt]

            target_state_single["LLA"] = LLA
            target_state_single["num"] = self.num
            if target_ID in self.detected_state2:
                # 那就是有的
                if "this" in self.detected_state2[target_ID]:
                    # 反正暴力出奇迹，只存两步，线性插值，怎么简单怎么来。
                    target_state["last"] = copy.deepcopy(self.detected_state2[target_ID]["this"])
            target_state["this"] = copy.deepcopy(target_state_single)
            self.detected_state2[target_ID] = target_state

        # 整个过滤机制，时间太长的探测信息就直接不保存了
        list_deleted = []
        for target_ID in self.detected_state2:
            if (self.num - self.detected_state2[target_ID]["this"]["num"]) > 500:
                # 姑且是500帧之前的东西就认为是没用了。
                list_deleted.append(target_ID)
        for target_ID in list_deleted:
            del self.detected_state2[target_ID]
        return

    def get_prior_list(self, type):
        # 这个是输入输入装备种类或者别的什么种类的字符串，输入一个目标优先级列表
        # 这个搞高级一点，输入个ID进来，然后根据自身弹量来确定优先级？不，不要搞乱了，这里只要优先级，能不能打到后面再判断
        if ("MainBattleTank" in type):
            # 有机械化突击能力的东西，就先打机械化的东西。
            if self.num < 1000:  # 先不打小车
                prior_list = ["MainBattleTank"]
            else:
                prior_list = ["MainBattleTank", "ArmoredTruck", "WheeledCmobatTruck", "Infantry", "missile_truck",
                              "Howitzer"]
        elif ("ArmoredTruck" in type):
            if self.num < 20:  # 先不打别的，就打防空车。
                prior_list = ["missile_truck"]
            else:
                prior_list = ["missile_truck", "MainBattleTank", "ArmoredTruck", "Infantry", "missile_truck",
                              "Howitzer"]
        elif ("Howitzer" in type) or ("Infantry" in type):
            prior_list = ["MainBattleTank", "ArmoredTruck", "WheeledCmobatTruck", "Infantry", "missile_truck",
                          "Howitzer"]

        elif ("ShipboardCombat_plane" in type):
            prior_list = []
            if self.num % 10 == 0:  # 这个没有CD，手动给它加个CD
                if self.num < 480:  # 先不打小车，反正打不中。
                    pass
                elif self.num < 1000:
                    prior_list = ["Howitzer"]
                else:
                    prior_list = ["missile_truck", "ArmoredTruck", "Howitzer", "Infantry"]


        elif ("Infantry" in type):

            if self.num < 100:  # 先打机械的
                prior_list = ["MainBattleTank", "ArmoredTruck", "WheeledCmobatTruck"]
            else:
                prior_list = ["MainBattleTank", "ArmoredTruck", "WheeledCmobatTruck", "missile_truck", "Howitzer",
                              "Infantry", ]

        elif ("missile_truck" in type):
            # 这玩意按说得防空，还得研究一下怎么个说法。
            # 根据子航的说法，防空和打击是不挨着的，防空是自动的。那直接把它当反装甲单位用也行咯。
            # 优先打击敌方火力单位好了。
            prior_list = ["missile_truck", "MainBattleTank", "Howitzer", "ArmoredTruck", "Infantry",
                          "WheeledCmobatTruck"]
        elif ("WheeledCmobatTruck" in type):
            # 只能打兵的，那就打兵了。
            # 子弹应该很难消耗完，所以子弹打到车上去了讲道理也不是很有所谓。
            prior_list = ["Infantry", "Truck", "Howitzer", "missile_truck", "MainBattleTank"]
        else:
            # 以防万一
            prior_list = ["missile_truck", "MainBattleTank", "Howitzer", "Infantry", "ArmoredTruck",
                          "WheeledCmobatTruck"]
        return prior_list

    def check_zhimiao(self, attacker_ID, target_ID, weapon_selected):
        # 这个用来判断是不是直瞄。
        # 确切地说，这个用来封装武器类型和直瞄间瞄是否匹配。匹配就输出true，不匹配就输出false
        # 返回true就可以开火了。
        flag_jieguo = False
        if (weapon_selected == "HighExplosiveShot") or \
                (weapon_selected == "ArmorPiercingShot") or \
                (weapon_selected == "ShortRangeMissile") or \
                (weapon_selected == "RPG"):
            # 这些属于是直瞄间瞄都可以的东西，所以直接返回通过check。
            flag_jieguo = True
        elif (weapon_selected == "HighExplosiveShot_ZT") or \
                (weapon_selected == "ArmorPiercingShot_ZT") or \
                (weapon_selected == "Bullet_ZT") or \
                (weapon_selected == "AGM"):
            # 这些是策略上只能允许直瞄的。如果选出来的目标构不成直瞄条件那还不如不瞄，因为站住了开间瞄会容易被打，还不一定能够命中
            # 在这个装备的探测池子里面的就是直瞄，不在的就认为是间瞄
            flag_detect = self.check_detect(attacker_ID, target_ID)
            if flag_detect:
                flag_jieguo = True
        else:
            # 子弹随便打，反正多的是。RPG要打引导射击。or (weapon_selected == "RPG")
            flag_jieguo = True

        return flag_jieguo

    def check_detect(self, attacker_ID, target_ID):
        # 这个就是单纯的测试这个有没有直接看到那个。
        # 甚至都没有必要区分具体是哪个探测器看到的。
        flag_jieguo = False
        attacker_detector_list = self.status[attacker_ID]["DetectorState"]
        for attacker_detectedinfo_single in attacker_detector_list:
            attacker_detected_units = attacker_detectedinfo_single["DetectedState"]
            for attacker_detected_unit in attacker_detected_units:
                # 遍历每个探测器的每一条目标
                if target_ID == attacker_detected_unit["targetID"]:
                    # 那就说明是探测到了，那就可以改标志位、返回了。
                    flag_jieguo = True
                    break

        return flag_jieguo

    def check_effect(self, enemy_ID, weapon_type):
        # 这个是用于避免没用的武器类型组合的。
        flag_effect = True
        if "ullet" in weapon_type:
            # 子弹只打步兵
            if "Infantry" in enemy_ID:
                pass
            else:
                flag_effect = False
        elif "ArmorPiercingShot" in weapon_type:
            # 穿甲弹不打步兵
            if "Infantry" in enemy_ID:
                flag_effect = False

        return flag_effect

    def select_by_type(self, type):
        # 就根据type过滤一个兵种集合出来。严格来说也不全是兵种，输入个数字1之类的也行。
        # 这个搭配group_A，兵力火力梯次配置就变得非常方便了。
        jieguo_status = {}
        for attacker_ID in self.status:
            if type in attacker_ID:
                # 说明是这个种类的不假
                jieguo_status[attacker_ID] = self.status[attacker_ID]

        return jieguo_status

    def check_all_finished(self, **kargs):
        # 这个是检验一下当前的抽象状态对应的命令是不是完成了.如果所有东西都是隐蔽的那个命令,就算是完成了.
        flag_finished = True
        if "status" in kargs:
            status_under_check = kargs["status"]
        else:
            status_under_check = self.status

        for attacker_ID in status_under_check:
            try:
                abstract_state_dic = self.abstract_state[attacker_ID]
                if abstract_state_dic["abstract_state"] != "hidden_and_alert" \
                        and abstract_state_dic["abstract_state"] != "partrol_and_monitor":
                    # if abstract_state_dic["flag_shelter"] == True:    # 还得分两行. # 还是不行,不然过去途中被击毁就卡住了
                    flag_finished = False
                    break
            except:
                abstract_state_dic = {}
                # 子弹导弹类的不过这个判定

        # 如果全都是hidden_and_alert状态,那就true,但凡有一个不是的,都不行.
        # 这个逻辑是有点问题的,如果有被打坏了动不了但是还没毁坏的车辆,则这个执行不了
        return flag_finished

    def __status_filter(self, status):
        # 这个用于滤除奇怪的东西.
        status_new = {}
        for attacker_ID in status:
            # 卫星、飞机,和bmc3是不吃这个指令的，还是区分一下以防后面报错在
            # 飞机还是应该吃这个指令
            flag = ("bmc" in attacker_ID) or ("satallite" in attacker_ID) or ("DespoilControlPos" in attacker_ID)  # \
            # or ("ShipboardCombat_plane" in attacker_ID) \
            # or ("missile_truck" in attacker_ID)
            if not flag:
                status_new[attacker_ID] = status[attacker_ID]
        return status_new

    def check_dian(self):
        status = self.status
        flag = False
        for attacker_ID in status:
            if ("DespoilControlPos" in attacker_ID):
                flag = True
                break
        return flag

    # xxh 1009 ,这里往后的部分,要是需要的话弄到其他的层次里面去,需要稍加注意.原则上后面都只操作status及其子集

    def F2A(self, target_LLA, **kargs):
        # 这个就是星际争霸语义下的F2A
        if "status" in kargs:
            status = kargs["status"]  # 这个是用来取一个装备的子集,试试行不行
        else:
            status = self.status

        for attacker_ID in status:
            self.set_move_and_attack(attacker_ID, target_LLA)

    def group_A(self, target_LLA, **kargs):
        # 阵而后战,兵法之常,运用之妙,存乎一心
        # 阵型是有方向的,这里应该先实现一个阵型框架,然后硬编码的整个数字
        if "status" in kargs:
            status = kargs["status"]  # 这个是用来取一个装备的子集,试试行不行
        else:
            status = self.status
        status = self.__status_filter(status)

        # 先求出一个方向
        # 整个自己的平均位置,后面这部分等子航他们聚类要是整好了就换个高级的
        LLA_average = self.get_LLA_ave(status)

        # 然后求一个方向出来.
        target_LLA = np.array(target_LLA)
        vector_LLA = target_LLA - LLA_average
        vector_LLA[2] = 0  # 投影到二维上
        vector_LLA = vector_LLA / np.linalg.norm(vector_LLA)  # 虽然未见得必要,但是还是归一化一下.

        # 然后开始布阵了
        vector_n_LLA = np.array([-1 * vector_LLA[1], vector_LLA[0], 0])  # 生成一个法向量
        # dL = 0.0003  # 别吃三十米的导弹aoe
        dL = 0.003  # 在此基础上加一点。

        # 先来个最基本的方方正正的好了,方阵往里面填就是了
        LLA_list = []
        for j in range(3):
            for i in range(5):
                d_vector = (-2 + i) * vector_n_LLA + (-1 + j) * vector_LLA
                d_LLA = d_vector * dL
                LLA_single = target_LLA + d_LLA
                LLA_list.append(LLA_single)

        ID_list = list(status.keys())
        # 然后开始往这一堆的点里面填充装备
        for i in range(min(len(status), len(LLA_list))):
            # 写成有序的形式是为了能够保证输入的序列顺序一样,输出的阵型形状就一样.

            attacker_ID = ID_list[i]  # 这里按说得有一个排序机制,体现出排阵型的策略.不过这个可以不用放在这里实现
            target_LLA = LLA_list[i]
            self.set_move_and_attack(attacker_ID, target_LLA)

        # 按理来说这个指令一发,都到位了就能看到阵型了,然后往前A,先到的就隐蔽起来等一下,好像也没有什么不好的.

    def group_A2(self, target_LLA, che_status, bing_status):
        # 这个是步兵和步战车专属的，丑陋可耻但有用。
        self.set_none(che_status)
        self.set_none(bing_status)

        che_ID_list = list(che_status.keys())
        bing_ID_list = list(bing_status.keys())
        geshu = min(len(che_status), len(bing_status))

        # 还是整个分散一下的东西。生成一个圆形的阵形
        LLA_list = self.__get_LLA_around(target_LLA, n_R=2, n_theta=3, dR=0.003)
        for i in range(geshu):
            self.set_charge_and_xiache(che_ID_list[i], bing_ID_list[i], LLA_list[i])

        # print("unfinished yet, agent.group_A2")
        pass

    def group_A_gai(self, target_LLA, status):
        # 这个是改进的group A，每次只A一小段那种，用于长途跋涉。
        # self.group_A_gai_config = {"target_LLA": [] ,
        #                            "start_LLA": [] ,
        #                            "target_LLA_next": [],
        #                            "flag_start": False,
        #                            "flag_end" : False,
        #                            "dL" : 0.008,
        #                            "dl_vector": [] }
        if self.group_A_gai_config["flag_end"] == True:
            # 来不及整理架构了，这个现在只能每把用一次，再要用要手动改这个config
            self.group_A_gai_config = {"target_LLA": [],
                                       "start_LLA": [],
                                       "target_LLA_next": [],
                                       "flag_start": False,
                                       "flag_end": True,
                                       "dL": 0.008,
                                       "dl_vector": []}
            return  # 跑完了就返回去。

        ave_LLA = self.get_LLA_ave(status)
        dL = self.group_A_gai_config["dL"]
        if self.group_A_gai_config["flag_start"] == False:
            # 那就是这个是第一步，初始化一下这些个状态。
            self.group_A_gai_config["flag_start"] = True
            self.group_A_gai_config["flag_end"] = False
            self.group_A_gai_config["target_LLA"] = np.array(target_LLA)

            dl_vector = target_LLA - ave_LLA
            dl_vector[2] = 0
            dl_vector = dl_vector / np.linalg.norm(dl_vector)
            # 求出方向然后归一化以备后用
            self.group_A_gai_config["dl_vector"] = dl_vector
            # 然后生成一个
            target_LLA_next = ave_LLA + dl_vector * dL
            self.group_A_gai_config["target_LLA_next"] = target_LLA_next
        else:
            target_LLA = self.group_A_gai_config["target_LLA"]
            target_LLA_next = self.group_A_gai_config["target_LLA_next"]
            dl_vector = self.group_A_gai_config["dl_vector"]
            jvli2 = self.distance(target_LLA_next[0], target_LLA_next[1], target_LLA_next[2],
                                  ave_LLA[0], ave_LLA[1], ave_LLA[2])

            if jvli2 < (dL / 180 * 3.1415926 * 6371000) * 0.6:
                jvli = self.distance(target_LLA[0], target_LLA[1], target_LLA[2],
                                     ave_LLA[0], ave_LLA[1], ave_LLA[2])

                if abs(jvli - jvli2) < dL * 0.5:
                    # 那就是到了，就得停了完事了
                    self.group_A_gai_config["flag_end"] = True
                else:
                    # 那就是到了一个点了，那就下一个点
                    target_LLA_next = ave_LLA + dl_vector * dL
                    self.group_A_gai_config["target_LLA_next"] = target_LLA_next
                    self.group_A(target_LLA_next, status=status)
            else:
                # 那就是没到，那就继续跑呗。
                if self.num % 14 == 0:
                    self.group_A(target_LLA_next, status=status)
                pass

        return

    def group_A_gai_reset(self):
        self.group_A_gai_config = {"target_LLA": [],
                                   "start_LLA": [],
                                   "target_LLA_next": [],
                                   "flag_start": False,
                                   "flag_end": False,
                                   "dL": 0.008,
                                   "dl_vector": []}

    def F2S(self):
        # 这个就是所有装备停止运动，而且是连hidden都停止，直接退出abstract state模式。
        # 这个就是星际争霸语义下的F2S
        for attacker_ID in self.status:
            self.set_none(attacker_ID)

    def group_S(self, **kargs):
        if "status" in kargs:
            status = kargs["status"]  # 这个是用来取一个装备的子集,试试行不行
        else:
            status = self.status
        for attacker_ID in status:
            self.set_none(attacker_ID)

    def group_D(self, **kargs):

        # 这个也是功能单一，就是收拢部队，成防御状态了。

        # 获取一些基础数据
        if "status" in kargs:
            status = kargs["status"]  # 这个是用来取一个装备的子集,试试行不行
        else:
            status = self.status
        geshu = len(status)

        # 求一下中心点什么的。
        # 整个自己的平均位置,不搞等靠要之类的玄学操作。
        LLA_average = self.get_LLA_ave(status)

        # 首先生成一个圆形的阵形
        LLA_list = self.__get_LLA_around(LLA_average, n_R=3, n_theta=5, dR=0.0005)

        # 然后把各种东西都A过来  # 开始往这一堆的点里面填充装备
        ID_list = list(status.keys())

        for i in range(min(len(status), len(LLA_list))):
            # 写成有序的形式是为了能够保证输入的序列顺序一样,输出的阵型形状就一样.
            attacker_ID = ID_list[i]  # 这里按说得有一个排序机制,体现出排阵型的策略.不过这个可以不用放在这里实现
            target_LLA = LLA_list[i]
            self.set_move_and_attack(attacker_ID, target_LLA)

    def get_LLA_ave(self, status={}):
        # 就是整一下平均数。

        if len(status) == 0:
            LLA_defualt = np.array([2.71, 39.76, 0])
            return LLA_defualt

        # 整个自己的平均位置,后面这部分等子航他们聚类要是整好了就换个高级的
        LLA_all = np.array([0, 0, 0])
        LLA_num = 0.00001
        for attacker_ID in status:
            LLA_single = self.__get_LLA(attacker_ID)
            LLA_single = np.array(LLA_single)

            LLA_all = LLA_all + LLA_single
            LLA_num = LLA_num + 1

        LLA_average = LLA_all / LLA_num  # 那这个就是作为阵型中心点的位置了

        return LLA_average

    def group_zhandian(self, status, target_LLA = [2.71, 39.76, 90]):
        # 这里整一个占点的东西，每一把都调用一次

        # 取出离点内最近的
        min_ID = ""
        min2_ID = ""
        min2_distance = 114514
        min_distance = 114514
        # target_LLA = [2.71, 39.76, 90]
        status = self.__status_filter(status)
        for attacker_ID in status:
            if "Ship" in attacker_ID:
                continue
            this_LLA = self.__get_LLA(attacker_ID)
            this_distance = self.distance(this_LLA[0], this_LLA[1], this_LLA[2]
                                          , target_LLA[0], target_LLA[1], target_LLA[2])
            if this_distance < min_distance:
                min2_distance = min_distance
                min_distance = this_distance
                min2_ID = min_ID
                min_ID = attacker_ID

        if min_distance > 100:
            self.set_move_and_attack(min_ID, target_LLA)
            # self.set_circle(min_ID, target_LLA)
            self.flag_zhandian = False
        else:
            self.flag_zhandian = True

        if min2_distance > 300:
            # target_LLA = [2.685, 39.70, 90]
            # self.set_move_and_attack(min2_ID, target_LLA)
            self.set_circle(min2_ID, target_LLA, R=0.01)

    def set_commands(self, command_list:list):
        print("set_commands: unfinished yet")
        # 首先把这些个command加入到queue里面去。增加一个键值对，当前时间。
        for coomand_single in command_list:
            coomand_single["step_num"] = self.num
            self.commands_queue.put(coomand_single)
        
        # 然后开始执行，具体的逻辑还得想想。
        pass
class landform_type(Enum):
    # 要比较优先级的，还是整个枚举类好了。
    construction = 0
    forest = 1
    river = 2
    covered_road = 3
    open_area = 4
    default = 5
    ocean = 6
    failed = 7
