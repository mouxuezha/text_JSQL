import os.path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import math
import copy
import numpy as np
import codecs
import sys, os
import xlrd
import queue
import time
import random
from enum import Enum

class BaseAgent(object):
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
        
        self.unit_type_list = ["WheeledCmobatTruck_ZB100", "WheeledCmobatTruck_ZB200", "ArmoredTruck_ZTL100", "missile_truck", "Infantry", "MainBattleTank_ZTZ100", "MainBattleTank_ZTZ200", "Howitzer_C100", "ShipboardCombat_plane", "JammingTruck","CruiseMissile"] 

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
        self.player = "undefined"
        
    
    def reset(self):
        self.infantry_tank_map = {}
        self.groupmap = {}
        self.act = []
        self.time_ = time.time()

        # 以下xxh定制，不保熟
        self.abstract_state = {}  # key 是装备ID，value是抽象状态        
        self.flag_zhandian = False
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
        self.detected_state = {}
        self.detected_state2 = {}  # 这个预计用于折腾什么路径规划啊那些。就key是ID，value是观测到的不同帧数的路径好了。

        # self.player = "undefined"


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

    # 移动指令
    def _Move_Action(self, Id, lon, lat, alt):
        # 巡飞弹单独处理，后端用的命令不一样。
        if "CruiseMissile" in Id:
            # MoveAction = {"Type": "CruiseMissileAct", "ID": Id, "Lon": lon, "Lat": lat, "Alt": alt, "AttackFlag": 0} # 1 是巡飞弹进攻，0是巡飞弹巡航。
            MoveAction = {"Type": "Move", "Id": Id, "Lon": lon, "Lat": lat, "Alt": 100.0}
        else:
            # 这个是一般的情况
            MoveAction = {"Type": "Move", "Id": Id, "Lon": lon, "Lat": lat, "Alt": alt}
            # self._exec_group_cmd(Id, "Move", **MoveAction)
        # MoveAction = {"Type": "Move", "Id": Id, "Lon": lon, "Lat": lat, "Alt": alt}
        self.act.append(MoveAction)  # xxh0906
        return MoveAction
    
    # 改变状态指令
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
        # 攻击指令也是，巡飞弹的由于后端命令不一样所以进行单独处理。
        if "CruiseMissile" in Id:
            AttackAction = {"Type": "CruiseMissileAct", "ID": Id, "Lon": lon, "Lat": lat, "Alt": alt, "AttackFlag": 1} # 1 是巡飞弹进攻，0是巡飞弹巡航。
            # 现版本接口事实上不需要Unit_Type
        else:
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
    
    # 删除编队指令
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

    # 干扰指令函数  0801ZY添加
    def _SetJammer_Action(self, Id, Pattern):
        _SetJammer_Action = {"Type": "Set_Jammer", "Id": Id,  "Pattern": Pattern} # 合理推测，开关是0、1，反正代码里是int，管他呢。
        self._exec_group_cmd(Id, "Set_Jammer", **_SetJammer_Action)
        self.act.append(_SetJammer_Action)
        return _SetJammer_Action

    # 进入建筑物指令函数  0801ZY添加
    def _PassInto_Action(self, Id, flag ):
        _PassInto_Action = {"Type": "Pass_Into", "Id": Id, "flag": flag}
        self._exec_group_cmd(Id, "Pass_Into", **_PassInto_Action)
        self.act.append(_PassInto_Action)
        return _PassInto_Action    

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
    
    def _status_filter(self, status):
        # 这个用于滤除奇怪的东西.
        status_new = {}
        for attacker_ID in status:
            # 初步过滤一下，弹药什么的不吃相关指令了
            flag = ("bmc" in attacker_ID) or ("satallite" in attacker_ID) or ("DespoilControlPos" in attacker_ID)  or ("Shot" in attacker_ID)  \
            # or ("ShipboardCombat_plane" in attacker_ID) or ("CruiseMissile" in attacker_ID) or ("buildings" in attacker_ID)\
            # or ("missile_truck" in attacker_ID)
            if not flag:
                status_new[attacker_ID] = status[attacker_ID]
        return status_new
    
    def get_detect_info(self, status):
        # LJD不会探测
        filtered_status = self._status_filter(self.status)
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
    
    def get_unit_type(self,unit_id):
        # 获取单位种类。
        for type_i in self.unit_type_list:
            if type_i in unit_id:
                return type_i
        
        return "invalid unit type"
    
    def unit_local_memory(self, status, **kargs):
        # 考虑一下，是否需要给人家留下扩展的空间。
        pass 

    def get_LLA(self, ID, **kargs):
        # 这个就是单纯的从status里面把LLA拿出来。
        if "status" in kargs:
            status = kargs["status"]
        else:
            status = self.status
        try:
            lon = status[ID]["VehicleState"]["lon"]
            lat = status[ID]["VehicleState"]["lat"]
            alt = status[ID]["VehicleState"]["alt"]
        except:
            # 直接用异常处理吧，来处理万一单位炸了之后会发生什么。
            lon = 0
            lat = 0
            alt = 0

        LLA = [lon, lat, alt]

        return LLA

    def select_by_type(self, type):
        # 就根据type过滤一个兵种集合出来。严格来说也不全是兵种，输入个数字1之类的也行。
        # 这个搭配group_A，兵力火力梯次配置就变得非常方便了。
        jieguo_status = {}
        for attacker_ID in self.status:
            if type in attacker_ID:
                # 说明是这个种类的不假
                jieguo_status[attacker_ID] = self.status[attacker_ID]

        return jieguo_status
    
    def Weapon_estimate(self, status, ID, missileType):  # 判断D是否耗尽
        type = True
        for i in range(len(status[ID]["WeaponState"])):
            if status[ID]["WeaponState"][i]['WeaponType'] == missileType+"_launcher" and \
                    status[ID]["WeaponState"][i]['WeaponNum'] == 0:
                type = False
        return type    

    def get_nearest(self, my_LLA, detectinfo:dict):
        # 预制一个“找到最近的敌方”的东西。
        jvli_list = []
        id_list = [] 
        id_nearest = "none"
        # distance
        for id_single in detectinfo:
            id_list.append(id_single)
            LLA_single = [detectinfo[id_single]["targetLon"],detectinfo[id_single]["targetLat"],detectinfo[id_single]["targetAlt"]]
            jvli_single = self.distance(my_LLA[0], my_LLA[1], my_LLA[2], LLA_single[0], LLA_single[1], LLA_single[2])
            jvli_list.append(jvli_single)
        
        # 然后找最近的.
        if len(jvli_list)>0:
            jvli_nearest = min(jvli_list)
            index_min = jvli_list.index(jvli_nearest)
            id_nearest = id_list[index_min]
        else:
            jvli_nearest = 1145141919
        
        return id_nearest,jvli_nearest

    def random_patrol(self, Id, patrol_area, num_points):
        lon_min, lon_max, lat_min, lat_max = patrol_area
        for _ in range(num_points):
            random_lon = random.uniform(lon_min, lon_max)
            random_lat = random.uniform(lat_min, lat_max)
            random_alt = 1000

            self._Move_Action(Id, random_lon, random_lat, random_alt)

