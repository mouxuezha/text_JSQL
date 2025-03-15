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
from support.tools import load_bridge_json

class BaseAgent(object):
    def __init__(self):
        self.infantry_tank_map = {}
        self.groupmap = {}
        self.act = []
        self.time_ = time.time()
        self.num = 0 

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
        self.group_A_gai_config = dict()
        self.group_A_gai_reset(name="red")
        self.group_A_gai_reset(name="blue")

        self.weapon_V = {"HighExplosiveShot_ZT": 1200, "HighExplosiveShot": 1000,
                         "ShortRangeMissile": 1800, "RPG": 245, "AGM": 680,
                         "ArmorPiercingShot_ZT": 1700, "ArmorPiercingShot": 1500,
                         "Bullet_ZT": 840, "bullet": 600,"CruiseMissile": 300}
        self.flag_zhandian = False

        self.commands_queue = queue.Queue(maxsize=114514) # 这个是新加的，用来处理和大模型的交互。
        self.player = "undefined" # red or blue
        self.role = "undefined" # global or local
        self.missile_truck_attacked = dict() # 这个用于红方记录打了多少个车，从而决定能不能开始发射导弹了。
        # 2024 our_duizhan
        self.building_loaction_list = [] 
        self.building_loaction_list.append([100.137777,13.6442,0])
        self.building_loaction_list.append([100.1644399,13.65847,0])
        self.building_loaction_list.append([100.103974397,13.63564213,0])
        self.building_loaction_list.append([100.1167513,13.6432282,0])
        self.building_loaction_list.append([100.140676439,13.607695814,0])

        self.bridge_location_list = load_bridge_json("beifen\\Bridge.json")
        # 算了这个直接读取JSON好了，不然一个一个复制粘贴不理想。


 
    def reset(self):
        self.infantry_tank_map = {}
        self.groupmap = {}
        self.act = []
        self.time_ = time.time()

        # 以下xxh定制，不保熟
        self.abstract_state = {}  # key 是装备ID，value是抽象状态        
        self.flag_zhandian = False
        # 就只存两帧，多的不要。
        self.group_A_gai_config = dict()
        self.group_A_gai_reset(name="red")
        self.group_A_gai_reset(name="blue")

        self.weapon_V = {"HighExplosiveShot_ZT": 1200, "HighExplosiveShot": 1000,
                         "ShortRangeMissile": 1800, "RPG": 245, "AGM": 680,
                         "ArmorPiercingShot_ZT": 1700, "ArmorPiercingShot": 1500,
                         "Bullet_ZT": 840, "bullet": 600,"CruiseMissile": 300}
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
    
    def distance2(self,LLA1,LLA2):
        # 这个和上面那个完全一样，单纯只是封装一下，让它调用的时候的参数列表不要显得那么的抽象。
        jieguo = self.distance(LLA1[0],LLA1[1],LLA1[2],LLA2[0],LLA2[1],LLA2[2])
        return jieguo 

    def m_to_degree(self,R_in_m):
        # 统一抽出来写一个，别在各种地方散落6371了。
        R_rad = R_in_m/6371000
        R_deg = R_rad / np.pi * 180  
        return R_deg
    
    def degree_to_m(self,R_deg):
        R_in_m = R_deg / 180 * 3.1415926 * 6371000
        return R_in_m
    
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
        # 在这里做一层兼容算了。
        if type(vehicleMoveState) == str:
            # 不能直接给到平台里面，得转成数字才能给到平台里面。
            if vehicleMoveState == "move":
                vehicleMoveState = 0
            elif vehicleMoveState == "stay":
                vehicleMoveState = 1
            elif vehicleMoveState == "hidden":
                vehicleMoveState = 2
            elif vehicleMoveState == "offroad":
                vehicleMoveState = 3
            else:
                raise Exception("base_agent: invalid vehicleMoveState in _Change_State")
            
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
    
    def _status_filter(self, status,model="enemy"):
        # 这个用于滤除奇怪的东西.model用来选择过滤滤掉一些什么东西。enemy状态服务于打对面，me状态服务于态势感知。主要的区别是要不要无人机和巡飞弹
        status_new = {}
        for attacker_ID in status:
            # 初步过滤一下，弹药什么的不吃相关指令了
            flag = ("bmc" in attacker_ID) or ("satallite" in attacker_ID) or ("DespoilControlPos" in attacker_ID)  or ("Shot" in attacker_ID) or ("buildings" in attacker_ID)
            if model == "enemy":
                flag = flag or ("ShipboardCombat_plane" in attacker_ID) or ("CruiseMissile" in attacker_ID)
            # or ("missile_truck" in attacker_ID)
            if not flag:
                status_new[attacker_ID] = status[attacker_ID]
        return status_new
    
    def get_detect_info(self, status):
        # LJD不会探测
        filtered_status = self._status_filter(self.status, model="me")
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
            if "this" in status[ID]:
                LLA = status[ID]["this"]["LLA"]
            else:
                lon = status[ID]["VehicleState"]["lon"]
                lat = status[ID]["VehicleState"]["lat"]
                if lon ==None: # 还有奇怪的没有抓到的异常，再处理一下。
                    lon = 0 
                if lat == None:
                    lat = 0 
                alt = status[ID]["VehicleState"]["alt"]
                LLA = [lon, lat, alt]
        except:
            # 直接用异常处理吧，来处理万一单位炸了之后会发生什么。
            LLA = [0, 0, 0]   
            print("get_LLA fail, attention")

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
    
    def select_by_devide(self,status):
        # 这个也是有用的小工具，把选好的兵种分成010101的两队。
        jieguo_status1 = {}
        jieguo_status2 = {}
        num_flag = True
        for attacker_ID in status:
            num_flag = not num_flag # 翻转一下标志位。
            if num_flag:
                jieguo_status1[attacker_ID] = status[attacker_ID]
            else:
                jieguo_status2[attacker_ID] = status[attacker_ID]

        return jieguo_status1, jieguo_status2
    
    def Weapon_estimate(self, status, ID, missileType):  # 判断D是否耗尽
        type = True
        for i in range(len(status[ID]["WeaponState"])):
            if status[ID]["WeaponState"][i]['WeaponType'] == missileType+"_launcher" and \
                    status[ID]["WeaponState"][i]['WeaponNum'] == 0:
                type = False
        return type    
    # 后面开始了，xxh常用的那套abstract_state的说法

    # xxh尝试整点儿复合命令
    def Gostep_abstract_state(self, **kargs):
        # 这个就用来维护这些复合的抽象命令吧。讲道理，这个直接放在step里面最后一行行吗？好像也没啥不行的。
        # xxh20240831，得想个办法把abstract_state同步到local的里面。

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
                    # 设成跟随的似乎好点。先假设之前的跟随还好使。
                    che_status = self.select_by_type("WheeledCmobatTruck")
                    che_ID_list = list(che_status.keys())
                    # abstract_state_new[attacker_ID] = {"abstract_state": "none"}
                    self.set_follow_and_defend(attacker_ID,che_ID_list[0] )
            else:
                # 下车之后的步兵在filtered_status有在abstract_state没有，得更新进去
                abstract_state_new[attacker_ID] = {}

        self.abstract_state = abstract_state_new

        # 抽象状态整理一下之后，通过communication功能给它更新到local的agent里面。
        # 这个功能放在communication里面了

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
                    # self.set_partrol_and_monitor(my_ID, self.__get_LLA(my_ID))
                    # 2024，没啥好润的了，这版应该是直接藏起来可也。
                    self.set_hidden_and_alert(my_ID)
                else:
                    # 对别的装备，如果是空的，就隐蔽起来。
                    self.set_hidden_and_alert(my_ID)
            else:
                # 实际的处理
                if my_abstract_state["abstract_state"] == "move_and_attack":
                    self.__handle_move_and_attack2(my_ID, my_abstract_state["target_LLA"])
                elif my_abstract_state["abstract_state"] == "hidden_and_alert":
                    self.__handle_hidden_and_alert(my_ID)  # 兼容版本的，放弃取地形了。
                elif my_abstract_state["abstract_state"] == "partrol_and_monitor":
                    self.__handle_partrol_and_monitor(my_ID, my_abstract_state["target_LLA"])
                elif my_abstract_state["abstract_state"] == "open_fire":
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
                elif my_abstract_state["abstract_state"] == "UAV_scout":
                    self.__handle_UAV_scout(my_ID, my_abstract_state["center_LLA"],my_abstract_state["R"],my_abstract_state["flag_circle"])
                elif my_abstract_state["abstract_state"] == "move_and_jammer":
                    self.__handle_move_and_jammer(my_ID, my_abstract_state["target_LLA"],my_abstract_state["model"],my_abstract_state["flag_on"])
        return self.act

    def Inint_abstract_state(self, status):
        # 初始化一下，先全都搞成就地隐蔽。
        # return
        for my_ID in status:
            # target_LLA = self.__get_LLA(my_ID)
            # self.set_hidden_and_alert(my_ID)
            self.set_none(my_ID)
            # target_LLA = [2.59, 39.72, 0]
            # self.set_partrol_and_monitor(my_ID, target_LLA)
    
    # 要舍得删繁就简。这就是git带给我的自信。
    def set_move_and_attack(self, attacker_ID, target_LLA):
        # 还得是直接用字典，不要整列表。整列表虽然可以整出类似红警的点路径点的效果，但是要覆盖就得额外整东西。不妥
        if (type(attacker_ID) == dict) or (type(attacker_ID) == list):
            # 说明是直接把status输入进来了。那就得循环。
            for attacker_ID_single in attacker_ID:
                if "Jamming" in attacker_ID_single:
                    # 做一层兼容，让干扰车走这个也能有点用。
                    self.set_move_and_jammer(attacker_ID,target_LLA,model=1)
                else:
                    self.abstract_state[attacker_ID_single] = {"abstract_state": "move_and_attack",
                                                            "target_LLA": target_LLA,
                                                            "flag_moving": False, "jvli": 114514}
        else:
            if "Jamming" in attacker_ID:
                # 做一层兼容，让干扰车走这个也能有点用。
                self.set_move_and_jammer(attacker_ID,target_LLA,model=2)
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
        # 不是原地坐下了，要找周围好的地形。2024年的版本里，房子的作用空前强化，这个得好好整整了。
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

        # 2024 :这个不要重复去设，不然时间刷掉了
        if "abstract_state" in self.abstract_state[attacker_ID]:
            if self.abstract_state[attacker_ID]["abstract_state"] == "charge_and_xiache":
                return
            elif self.abstract_state[attacker_ID]["abstract_state"] == "move_and_attack":
                if self.abstract_state[attacker_ID]["next"]["abstract_state"]=="charge_and_xiache":
                    return # 这个也得加，不然状态反复横跳造成上车了但是不走。
        
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
        if R<1:
            # 那就认为是度数
            R_deg = R
        else:
            # 那就认为是输入的是米 
            R_deg = self.m_to_degree(R)  
        if (type(attacker_ID) == dict) or (type(attacker_ID) == list):
            # 说明是直接把status输入进来了。那就得循环。
            for attacker_ID_single in attacker_ID:
                self.abstract_state[attacker_ID_single] = {"abstract_state": "circle",
                                                           "R":R_deg,
                                                           "point_list": {},
                                                           "index": 0,
                                                           "target_LLA": target_LLA}
        else:
            self.abstract_state[attacker_ID] = {"abstract_state": "circle",
                                                "R": R_deg,
                                                "point_list": {},
                                                "index": 0,
                                                "target_LLA": target_LLA}
        pass

    def set_UAV_scout(self, attacker_ID, center_LLA, R=3000):
        # 察打一体无人机都是走这个，躲避电子干扰，躲避对面防空，点亮对面装备。这个好好搞搞，作为set circle 的上位替代。
        # 但是也有点区别，察打一体无人机可以择机开火，巡飞弹就先别开火。
        # 这里的半径直接用米了。
        # if R<1:
        #     # 那就认为是度数
        #     R_deg = R
        # else:
        #     # 那就认为是输入的是米
        #     R_deg =self.m_to_degree()
        if (type(attacker_ID) == dict) or (type(attacker_ID) == list):
            # 说明是直接把status输入进来了。那就得循环。
            for attacker_ID_single in attacker_ID:
                self.abstract_state[attacker_ID_single] = {"abstract_state": "UAV_scout",
                                                           "R": R,
                                                           "flag_circle": True, # 这个是用来标记顺时针还是逆时针的。True是顺时针
                                                           "center_LLA": center_LLA,
                                                           "flag_done": False, # 这个用来标记巡飞弹是不是用过了。
                                                           "turn_cd" : 0 # 这个是用来防止转方向转不过去了卡在边上的。
                                                           }
        else:
            self.abstract_state[attacker_ID] = {"abstract_state": "UAV_scout",
                                                           "R": R,
                                                           "flag_circle": True, # 这个是用来标记顺时针还是逆时针的。True是顺时针
                                                           "center_LLA": center_LLA,
                                                           "flag_done": False, # 这个用来标记巡飞弹是不是用过了。
                                                           "turn_cd" : 0 # 这个是用来防止转方向转不过去了卡在边上的。
                                                           }
        # 逻辑就是，顺着圆的走切线，有威胁就往外，到地图边上就反向。多搞点向量运算。
        pass

    def set_move_and_jammer(self, attacker_ID, target_LLA, model):
        # 有需求的情况下，给它开开关关闪死对面，鉴定为电磁压制。
        if (type(attacker_ID) == dict) or (type(attacker_ID) == list):
            # 说明是直接把status输入进来了。那就得循环。
            for attacker_ID_single in attacker_ID:
                self.abstract_state[attacker_ID_single] = {"abstract_state": "move_and_jammer", "model": model, "target_LLA":target_LLA,"flag_on":False}
        else:
            self.abstract_state[attacker_ID] = {"abstract_state": "move_and_jammer", "model": model, "target_LLA":target_LLA,"flag_on":False}
        # 逻辑就是，检测到周围值得干扰的目标就进入电磁压制状态，然后开开关开关关开。
        # 参数model就用来处理到底是怎么个开关法。
        # 1：只有看到威胁的时候开几秒，然后赶紧关了。2：保持压制，随机的开开关开关关开
        pass

    def __handle_move_and_jammer(self, attacker_ID, target_LLA, model, flag_on):
        # 第一部分，开过去，到了就隐蔽。开着就机动，关着就隐蔽。
        attacker_LLA = self.__get_LLA(attacker_ID)
        if type(target_LLA) is str:
            # 那就说明输入的是ID了，那就需要转化一下了。也是这么搞一下，这么搞一下之后该命令直接就可以支持追踪使用了。
            target_LLA = self.__get_LLA(target_LLA)
        # check一个距离看看到了是没到。
        if self.num % 114 == 0: # 量入为出，适度消费。能省点儿计算量是点儿，也不差这几秒。
            jvli = self.distance2(attacker_LLA, target_LLA)
            if(jvli<114.514):
                # 那就认为是到了。到了就是原地隐蔽吃减伤。
                self._Change_State(attacker_LLA, "hidden")
            else:
                # 那就是没到，没到就过去
                self._Move_Action(attacker_ID, target_LLA[0], target_LLA[1], target_LLA[2])
        

        # 第二部分：根据敌情释放干扰
        enemy_ID_nearst = "" # 这个是用于存“对我有威胁的最近一个敌方防空的ID”
        jvli_nearest = 114514 
        for enemy_id_single in list(self.detected_state2.keys()): # 顺利的话，见过一次的敌方防空车都是在这里面的。
            if ("CruiseMissile" in enemy_id_single) or ("Combat_plane" in enemy_id_single):
                # 那就说明这个是有危险的了，就得check一下距离
                # enemy_LLA = self.get_LLA(enemy_id_single,status=self.detected_state2)
                enemy_LLA = self.detected_state2[enemy_id_single]["this"]["LLA"]
                jvli = self.distance2(attacker_LLA, enemy_LLA)
                if jvli < 2000: # 别接近到它的射程内，如果接近到了，就要考虑赶紧跑路了
                    if jvli < jvli_nearest:
                        # 那就说明要更新最近的那个了。
                        jvli_nearest = jvli
                        enemy_ID_nearst = enemy_id_single
        
        if jvli_nearest<2000:
            # 这个就说明是危险的东西靠近到足够近的位置了
            # 那就看现在是什么模式
            if model == 1:
                # 那就是“遇到危险就开干扰”的模式
                self._SetJammer_Action(attacker_ID, 2)
                self.abstract_state[attacker_ID]["flag_on"] == True
            elif model == 2:
                # 那就是开了就关关了就开，而且加一个随机数
                flag_random = np.random.randint(0,5)
                if(flag_random>3):
                    if flag_on:
                        self._SetJammer_Action(attacker_ID, 0)
                        self.abstract_state[attacker_ID]["flag_on"] == False
                    else:
                        self._SetJammer_Action(attacker_ID, 2)
                        self.abstract_state[attacker_ID]["flag_on"] == True
            elif model == 0:
                # 调试用的，就是直接关了，不开干扰。
                pass
        if model == -1:
            # 调试用的，到一定步数就打开，不到就别开。
            if self.num > 114.514:
                self._SetJammer_Action(attacker_ID, 2)
                self.abstract_state[attacker_ID]["flag_on"] == True

        
    
    def __handle_UAV_scout(self, attacker_ID, center_LLA, R, flag_circle):
        # 这里具体来实现无人机绕飞侦察。# 增加一点泛用性，center_LLA也可以用己方ID，来实现跟着绕飞。
        attacker_LLA = self.__get_LLA(attacker_ID)

        if type(center_LLA) is str:
            # 那就说明输入的是ID了，那就需要转化一下了。
            center_LLA = self.__get_LLA(center_LLA)

        flag_attack = True  # 调试，开始打炮了。
        if flag_attack:
            flag_done = self.__handle_one_shot_attack(attacker_ID)
            if flag_done and "CruiseMissile" in attacker_ID:
                # 巡飞弹用了就用了，用了再发move指令我怕它抽风。
                self.abstract_state[attacker_ID]["flag_done"] = False
                return
        else:
            print("XXHtest: attack disabled in __handle_UAV_scout")
        
        # 巡飞弹防止命令嵌套。
        if self.abstract_state[attacker_ID]["flag_done"]:
            return

        # 先操作一下，是不是靠边了，如果是靠边了，就要换方向了。
        # mod_num = random.randint(0,10) # 这个改成随机也是为了防止在边上转来转去。但是效果不好反而飞出去了
        # 算了，不偷懒了，强行规定一个，转方向有CD
        mod_num = 0 
        if self.num % 1 == mod_num:
            # 这里参数得弄好，不然会出现转完了下一步还满足转的条件，就一直在边上转来转去。
            flag_edge = self.check_edge(attacker_ID,d_l=0.004) # 不用去的太靠边也行的奥。
            flag_distance = self.check_distance(attacker_ID,d_l=3000) # 检测一下当前单位和地面单位集群的平均距离，如果距离大了就转弯。

            if flag_edge or flag_distance:
                # 把这个flag换了.在特定条件下改变飞的方向。这样不会飞到太远的没有意义的地方去应该。
                self.abstract_state[attacker_ID]["flag_circle"] = not flag_circle
        
        
        # 先判断个距离，如果要是离得还远，那就先飞过去
        jvli = self.distance2(attacker_LLA, center_LLA)
        if jvli>R:
            # 那就是还没到，那去的方向就是奔着center去
            center_LLA[2] = 0 
            attacker_LLA[2] = 0 
            n_vector = np.array(center_LLA) - np.array(attacker_LLA)
            n_vector = n_vector / np.linalg.norm(n_vector)

            # 来点儿地转偏向力。
            n_vector_tan_origin = self.get_n_vector_tan(attacker_LLA, center_LLA) # 这个就是没有修改过的方向
            # 然后顺时针逆时针
            if flag_circle:
                n_vector_tan_origin = n_vector_tan_origin*(-1) 

            n_vector = n_vector_tan_origin*0.3 + n_vector*0.7 # 让它能够向外点去，拉开距离
            # 确实，加了这个之后不会有原地卡住了，卡着也会逐渐移动，一直到退出卡顿。鉴定为舒服。

        else:
            # 那就是距离已经到了，那就改成走切线方向了
            n_vector_tan_origin = self.get_n_vector_tan(attacker_LLA, center_LLA) # 这个就是没有修改过的方向

            # 然后根据探测到的威胁进行调整。遍历探测到的东西，把距离靠近到有威胁的东西弄出来，
            # 然后根据这个距离最近的的东西重新求一个切线的向量出来。相当于一段一段的飞小圆弧，逻辑上比较通顺。
            enemy_ID_nearst = "" # 这个是用于存“对我有威胁的最近一个敌方防空的ID”
            jvli_nearest = 114514 
            jvli_nearest_threshold = 123
            for enemy_id_single in list(self.detected_state2.keys()): # 顺利的话，见过一次的敌方防空车都是在这里面的。
                if ("missile_truck" in enemy_id_single) and ("Combat_plane" in attacker_ID):
                    jvli_threshold = 2000
                    flag_check = True
                    jvli_nearest_threshold = 2000 # 这个是防空导弹范围。
                elif ("JammingTruck" in enemy_id_single) and ("CruiseMissile" in attacker_ID): 
                    jvli_threshold = 2300
                    flag_check = True
                    jvli_nearest_threshold = 2300 # 讲道理这个是干扰范围。
                else:
                    flag_check=False
                    

                if flag_check == True:
                    # 那就说明这个是有危险的了，就得check一下距离
                    enemy_LLA = self.get_LLA(enemy_id_single,status=self.detected_state2)
                    # enemy_LLA = self.detected_state2[enemy_id_single]["this"]["LLA"] # 
                    jvli = self.distance2(attacker_LLA, enemy_LLA)
                    if jvli < jvli_threshold: # 别接近到它的射程内，如果接近到了，就要考虑赶紧跑路了
                        if jvli < jvli_nearest:
                            # 那就说明要更新最近的那个了。
                            jvli_nearest = jvli
                            enemy_ID_nearst = enemy_id_single
            # 至此搜完了，最有威胁的敌方防空应该应该是搜出来了
            if jvli_nearest < jvli_nearest_threshold:
                # 那就是搜到了，那就采取措施
                enemy_LLA = self.get_LLA(enemy_ID_nearst,status=self.detected_state2)
                n_vector_tan = self.get_n_vector_tan(attacker_LLA, enemy_LLA)
                # 干脆法向切向都弄出来
                n_vector_n = np.array(enemy_LLA) - np.array(attacker_LLA)
                n_vector_n = n_vector_n / np.linalg.norm(n_vector_n) 
                # 增加一个逻辑，比较修改前后的方向，取他们内积为正的那边，防止巡飞弹反复横跳。
                if np.dot(n_vector_tan, n_vector_tan_origin)>0:
                    # 那就说明方向是还可以
                    pass
                else:
                    n_vector_tan = n_vector_tan*(-1) 
                
                
                
            else:
                # 那就是说没有监测到新的需要威胁的。
                n_vector_n = np.array([0,0,0])
                n_vector_tan = n_vector_tan_origin
            # 然后顺时针逆时针
            if flag_circle:
                n_vector_tan = n_vector_tan*(-1) 

            n_vector = n_vector_tan*0.6 + n_vector_n*0.4 # 让它能够向外点去，拉开距离

        # 然后这里定出了方向，后面就是往那个方向走一段。
        if self.num %  2 == 0 : # 或许不用每一步都做这个决策。节省一些运算量也是好的。
            target_LLA = attacker_LLA + n_vector * 0.01
            self._Move_Action(attacker_ID, target_LLA[0], target_LLA[1], target_LLA[2])

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
                             attacker_LLA[0], attacker_LLA[1], target_LLA[2])  # 这里alt两个用成一样的，防止最后结束不了。
        if jvli > 25:
            # 那就是还没到，那就继续移动
            # 来个平滑化机制，来让它分散在不同的范围内
            mod_num = random.randint(1,20)

            if (self.num % 300 == mod_num) and (self.abstract_state[attacker_ID]["flag_moving"] == False) :
                # 那就是没动起来，那就得让它动起来。
                rand_dl_1 = random.randint(-5,5) * 0.0001
                rand_dl_2 = random.randint(-5,5) * 0.0001
                self._Move_Action(attacker_ID, target_LLA[0]+rand_dl_1, target_LLA[1]+rand_dl_2, target_LLA[2])
                self.abstract_state[attacker_ID]["flag_moving"] = True                
                # if (self.num<3000) or (self.num%114==0):
                #     # # 加点随机，这样应该动起来的概率能大一些。
                #     rand_dl_1 = random.randint(-5,5) * 0.0001
                #     rand_dl_2 = random.randint(-5,5) * 0.0001
                #     self._Move_Action(attacker_ID, target_LLA[0]+rand_dl_1, target_LLA[1]+rand_dl_2, target_LLA[2])
                #     self.abstract_state[attacker_ID]["flag_moving"] = True

                # elif (self.num%114==50):
                #     # 另一种策略，卡了之后往自己周围走一段看看。
                #     rand_dl_1 = random.randint(-5,5) * 0.001
                #     rand_dl_2 = random.randint(-5,5) * 0.001
                #     self._Move_Action(attacker_ID, attacker_LLA[0]+rand_dl_1, attacker_LLA[1]+rand_dl_2, attacker_LLA[2])
                #     self.abstract_state[attacker_ID]["flag_moving"] = True    

                # 这个机制似乎影响了A正面，感觉不是很理想。
                pass
                            
                
            # if (self.abstract_state[attacker_ID]["jvli"] == jvli) and (self.num>700):
            if (self.abstract_state[attacker_ID]["jvli"] == jvli) and (self.num>300):
                # self.__finish_abstract_state(attacker_ID)
                # 这里面是存着的距离等于这次的距离，那就认为是没动，改标志位准备走
                self.abstract_state[attacker_ID]["flag_moving"] = False # 那就认为是停了，卡住了
                pass 
            else:
                # 那就把距离更新过去。
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
                        # 巡飞弹的话还得check一下目标是不是在敌方干扰的覆盖范围内。
                        flag_ganrao = self.check_CruiseMissile_ganrao(attacker_ID, target_ID_local)
                        flag_done = flag_done and flag_ganrao
                        if flag_done:  # 根据策略，武器类型和直瞄间瞄是不是匹配。如果判出来彳亍就打
                            self._Attack_Action(attacker_ID, target_LLA_local_modified[0], target_LLA_local_modified[1],
                                                target_LLA_local_modified[2], weapon_selected)
                            
                            self.__handle_mul_shot_attack(attacker_ID, target_ID_local,target_LLA_local_modified, weapon_selected) # 这个是补刀用的。
                            
                            # 2024，增加一个记录函数，用来记打了几次导弹车，从而间接判断毁伤了多少导弹车。
                            self.check_attack_missile_truck(weapon_selected, target_ID_local)
                            self.check_attack_all(weapon_selected, target_ID_local) # 干脆都记录了算了。

                            break  # 打出来了，那就完事了
            if flag_done:
                # 开过火就变回去
                # self._Change_State(attacker_ID, "hidden")  # 这个写法会造成迫榴炮直接停下来打炮。
                # self.abstract_state[attacker_ID]["flag_shelter"] = True

                # 直接change成hidden似乎会导致直接停下不走了。
                if "target_LLA" in self.abstract_state[attacker_ID]:
                    # 试一下，开完火继续走。原则上这个不会破坏group A，但是会增加路径规划的调用次数
                    target_LLA = self.abstract_state[attacker_ID]["target_LLA"]
                    # 为了防止一直重复调用，这里也再加一些过滤。
                    if self.num % 100 == 49:
                        self._Move_Action(attacker_ID, target_LLA[0], target_LLA[1], target_LLA[2])
                pass 
        else:
            pass

        return flag_done
    
    def __handle_mul_shot_attack(self, attacker_ID, target_ID_local,target_LLA_local_modified, weapon_selected):
        # 这个是打个补丁，用于实现坦克和炮的连续开火的。
        # 说法应该是，目标如果是车辆，就补上一发高爆弹。
        if "ZTZ" in target_ID_local:
            if (weapon_selected == "ArmorPiercingShot"):
                # 那就是坦克打坦克，那就再补一发爆炸弹。
                weapon_selected2 = "HighExplosiveShot"
            elif(weapon_selected == "ArmorPiercingShot_ZT"):
                weapon_selected2 = "HighExplosiveShot_ZT"
            else:
                # 那就是不需要触发追加射击。
                weapon_selected2 = "none"
            
            if not (weapon_selected2 == "none"):
                self._Attack_Action(attacker_ID, target_LLA_local_modified[0], target_LLA_local_modified[1],
                                                target_LLA_local_modified[2], weapon_selected2)


    def __handle_hidden_and_alert(self, attacker_ID, GetLandForm=0):
        # 在这里集成一个“寻找周围安全区域”的逻辑

        # 卫星、飞机和bmc3是不吃这个指令的，还是区分一下以防后面报错在
        flag = ("bmc" in attacker_ID) or ("HEO_infrared_satallite" in attacker_ID) or (
                "ShipboardCombat_plane" in attacker_ID)
        if flag:
            return

        # 还可以优化。没必要每一步都求一次，只需求随便求几次，收敛了就罢了。
        if self.abstract_state[attacker_ID]["flag_shelter"] == False:
            LLA_here = self.__get_LLA(attacker_ID)
            if "Infantry" in attacker_ID:
                LLA_shelter, shelter_flag = self.__get_shelter(LLA_here, GetLandForm)
            else:
                LLA_shelter = LLA_here
                shelter_flag = True
            if shelter_flag:
                # 到了，隐蔽起来了，就把参数改了，然后隐蔽起来
                self.abstract_state[attacker_ID]["flag_shelter"] = True
                if "Infantry" in attacker_ID:
                    self._PassInto_Action(attacker_ID,1) # 没进房子就要进个房子，然后隐蔽，吃满加成

                self._Change_State(attacker_ID, "hidden")
            else:
                # 还没到，那就移动过去。
                # 本来应该是移动攻击过去，但是防止抽象命令互相调用，直接挪过去好了。
                if self.num % 49 == 7:
                    self._Move_Action(attacker_ID, LLA_shelter[0], LLA_shelter[1], LLA_shelter[2])

        # 然后，如果攻击范围里有敌人，就找个合适的打。这段跟搜索攻击里面攻击那段是一样的。
        flag_done = self.__handle_one_shot_attack(attacker_ID)

        return

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
                    LLA_around_list = self.__get_LLA_around(target_LLA, n_R=1, n_theta=1, dR=0.005)
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

    def __handle_open_fire2(self, attacker_ID):
        WeaponState_list = self.status[attacker_ID]["WeaponState"]
        # 2024：这里对导弹车进行一些单独的处理。导弹车只有在对方防空受到一定的削弱之后才会发射。
        if "missile_truck" in attacker_ID:
            # 如果我方是导弹发射车，就要看看对方防空情况，再决定是不是要打出去。
            num_attacked = 0 # 这个是敌方防空已被摧毁的数量 
            for ids in self.missile_truck_attacked:
                if self.missile_truck_attacked[ids] > 0 :
                    # 这里调一下参数看多少比较合适。
                    num_attacked = num_attacked + 1
            
            if num_attacked>=2: # 这儿的参数也是还得改改的。表示对方削弱到什么程度了之后才可以愉快地打导弹。
                # 进到这里就是可以愉快地打了
                pass # 所以往后执行以复用之前的代码
            else:
                # 不满足，那就是打不了，那就返回了。
                return
        
        # 还得是停下来才能打，需要处理一下强制停止的逻辑
        if self.num % 11 == 4:
            # 咱这里没有庙算里那种强制停止指令。所以应该是changestate来做。
            self._Change_State(attacker_ID, "stay")
            # self._Change_State(attacker_ID, "hidden")
        
        # 后面是真正的通用的执行开火的程序。
        geshu = len(WeaponState_list)
        # 这个的说法就是，有多少能打的就全都打一遍。虽然会有很多冗余指令，但是管他呢
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
        jvli2 = self.distance(attacker_LLA[0], attacker_LLA[1], attacker_LLA[2],
                                      target_LLA[0], target_LLA[1], attacker_LLA[2])
        if(jvli+jvli2<114.514):
            # 那就是已经到了，还搞个毛直接退了.顺手打一炮。
            self.__handle_one_shot_attack(infantry_ID)
            self.__finish_abstract_state(attacker_ID)
            return
        
        if flag_state == 1:
            # 没上车且距离远，那就得过去。
            if (jvli < 100) and (self.status[infantry_ID]["FatherID"] == ""):
                # 那就是到了，且没有上车，转变为可以上车的状态。
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
                if self.status[infantry_ID]["FatherID"] != "":
                    # 那就是对应的步兵已经没了，上车完成或者是真的没了。转换一下。
                    # 2024 ：今年设定变了，上车之后的步兵还是在态势里，所以要check一下fatherID了
                    flag_state = 3
                    self.abstract_state[attacker_ID]["flag_state"] = flag_state
                elif jvli < 100:
                    # 那就是到了，那就上车。
                    # self._Change_State(attacker_ID, "stay")
                    # self._Change_State(infantry_ID, "stay")
                    self._On_Board_Action(attacker_ID, infantry_ID)
                    self.abstract_state[attacker_ID]["num_wait"] = 5                    
                elif jvli <= 30000:
                    # 那就是没到且可以去。
                    flag_state = 1
                    self.abstract_state[attacker_ID]["flag_state"] = flag_state                    
            pass
        if flag_state == 3:
            # 开冲。 如果到了就放下来分散隐蔽，兵力分散火力集中。
            # 不要再闭环到1了，这样防止这东西死循环。
            if self.abstract_state[attacker_ID]["num_wait"] > 0:
                # 那就是等着呢，那就等会儿好了。
                self.abstract_state[attacker_ID]["num_wait"] = self.abstract_state[attacker_ID]["num_wait"] - 1
                if self.abstract_state[attacker_ID]["num_wait"]==0:
                    # 这一步减完了之后等于0，那就说明是应该退出这个状态了。
                    self.__finish_abstract_state(attacker_ID)
                    return
            else:
                
                if jvli2 < 100:
                    # 那就算是到了，没必要搞出奇怪的东西
                    # 到了就下车隐蔽
                    self._Change_State(attacker_ID, "stay")
                    # self._Change_State(infantry_ID, "stay")
                    self._Off_Board_Action(attacker_ID, infantry_ID)
                    self.abstract_state[attacker_ID]["num_wait"] = 5
                    # 得重新设计退出机制。2024.

                    # if jvli < 20000:
                    #     # 说明步兵ID已经有了，那就是下车成功了或者无论如何，反正步兵在地上。
                    #     # 而且没有敌人，先结束，原地藏起来。原地藏起来隐含了有敌人就A过去，所以不用单独写有敌人就A过去了。
                    #     # 这么写的话就可以中途搞几次下车警戒之类的，也没啥不好的。
                    #     self.__finish_abstract_state(attacker_ID)
                    #     self.__finish_abstract_state(attacker_ID)
                    #     # 这里存在一个问题，下车完成之后车本身是move_and_attack,而charge_and_xiache在抽象状态里面，所以要结束两次

                    #     # self.__finish_abstract_state(infantry_ID) # Python不让我直接这么玩。彳亍口巴
                    # else:
                    #     # 那就是没步兵了反正。
                    #     # self.__finish_abstract_state(attacker_ID)
                    #     # self.__finish_abstract_state(attacker_ID)
                    #     pass
                else:
                    # 进堆栈，A过去。   
                    abstract_state_next = copy.deepcopy(self.abstract_state[attacker_ID])
                    self.set_move_and_attack(attacker_ID, target_LLA)
                    self.abstract_state[attacker_ID]["next"] = abstract_state_next  # 然后把它放回去，准备跑完了之后再复原。
            pass
        return
    
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
            if jvli < 0.08*R:
                # 到了
                index = index + 1
                if index >= geshu:
                    index = 0

                # 这里如果是move_and_attack，就得把它结束掉。
        self.abstract_state[attacker_ID]["index"] = index
        point_next = point_list[index]
        self._Move_Action(attacker_ID, point_next[0], point_next[1], point_next[2])

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
        if "CruiseMissile" in attacker_ID:
            # 巡飞弹要单独处理。反正平台里不读取这个字段，无所谓了。
            selected_weapon = "CruiseMissile"
        else:
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
                            enemy_distance < 2000 * bili)) \
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
        # bili = 0.95  # 不要极限距离开火的超参数
        bili = 0.95 # 2024年，弹药相对来说是足够的，因此距离可以放开了，不用再压制自己的火力了，可以拼一枪。
        enemy_LLA_selected = [0, 0, 0]

        # 方案2，尝试加入优先级。
        # 方案2改，这个是改了发现概率之后。恐怕目标ID还不能只从当前帧的位置来，因为现在detectinfo里面的变量是若有若无的。
        # 方案2改2，这个是增加了子弹不打车的，或者说无效的就不打。
        # 2024：增加一个说法，识别目标是不是静止的。AGM之类的是想让它只炸静止的目标。
        prior_list = self.get_prior_list(attacker_ID)
        for i in range(len(prior_list)):
            prior_str = prior_list[i]  # 其实就是根据优先级多做几次方案1，而已。
            flag_select_prior = False
            # for enemy_ID in detectinfo:
            for enemy_ID in self.detected_state2:
                # 检测这个目标是不是新鲜的。
                if self.detected_state2[enemy_ID]["this"]["num"] < self.num - 500:
                    # 就说明目标信息已经不新鲜了，就不打了 # 正常情况下，这里面有的肯定都有this属性
                    # 如果这帧是能够detectinfo里有的，那肯定已经更新到deteced_state2里面了。
                    continue

                # 如果目标是新鲜的，就检测是不是合适打。
                attacker_LLA = self.__get_LLA(attacker_ID)
                target_LLA = self.detected_state2[enemy_ID]["this"]["LLA"]
                
                flag_enemy_stay = False
                # 检测一下，目标是不是固定的。如果是固定的就改个flag。
                try:
                    target_LLA_last = self.detected_state2[enemy_ID]["last"]["LLA"]
                except:
                    target_LLA_last = target_LLA
                # 坐标取出来之后直接比较了。复用距离程序
                enemy_distance_last = self.distance(target_LLA[0], target_LLA[1], target_LLA[2],
                                    target_LLA_last[0], target_LLA_last[1], target_LLA_last[2])
                if enemy_distance_last<0.1:
                    # 还是来个容错，不要求完全相等
                    flag_enemy_stay =True # 那就认为目标是静止的。


                enemy_distance = self.distance(target_LLA[0], target_LLA[1], target_LLA[2],
                                               attacker_LLA[0], attacker_LLA[1], attacker_LLA[2])
                flag_select = False
                # 在当前逻辑下，只要找最大范围内的就行了。
                if (enemy_distance < enemy_distance_min) and (prior_str in enemy_ID):
                    flag_select = (("MainBattleTank" in attacker_ID) and (enemy_distance < 2000 * bili)) \
                                  or (("Howitzer_C100" in attacker_ID) and (enemy_distance < 3000 * bili)) \
                                  or (("ArmoredTruck" in attacker_ID) and (enemy_distance < 1000 * bili)) \
                                  or (("WheeledCmobatTruck" in attacker_ID) and (enemy_distance < 700 * bili)) \
                                  or (("Infantry" in attacker_ID) and (enemy_distance < 800 * bili)) \
                                  or (("missile_truck" in attacker_ID) and (enemy_distance < 600000 * bili)) \
                                  or (("ShipboardCombat_plane" in attacker_ID) and (enemy_distance < 2000 * bili)) \
                                  or (("CruiseMissile" in attacker_ID) and (enemy_distance < 3000 * bili))
                    # or (("ShipboardCombat_plane" in attacker_ID) and (enemy_distance < 15000 * bili))
                    
                    # 增加一个处理，如果自己是无人机，那就只打静止的目标。
                    if ("ShipboardCombat_plane" in attacker_ID) or ("CruiseMissile" in attacker_ID):
                        flag_select = flag_select and flag_enemy_stay

                if flag_select:
                    enemy_distance_min_list.append(enemy_distance)
                    enemy_ID_selected_list.append(enemy_ID)
                    enemy_LLA_selected_list.append(target_LLA)

            # # 算了一步到位直接，有几个要几个。
            # if len(enemy_ID_selected_list)>=5:
            #     # 找五个选一个很给面子了，还想咋样嘛。
            #     break
        # 增加一个处理：如果自己是导弹车，那么事实上不需要根据距离来选，那么就是取靠前的几个，然后洗牌
        if "missile" in attacker_ID:
            index_max = min(6, len(enemy_ID_selected_list))
            ID_list = enemy_ID_selected_list[0:index_max]
            random.shuffle(ID_list)
            enemy_ID_selected_list[0:index_max] = ID_list
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
        if "Short" in weapon_selected or "RPG" in weapon_selected or "CruiseMissile" in weapon_selected:
            return target_LLA_local

        # 增加一版专业的加减乘除一下的，
        V_dan = self.weapon_V[weapon_selected]
        # attacker_LLA = self.__get_LLA(attacker_ID)
        # L_dan = self.distance(target_LLA_local[0], target_LLA_local[1], target_LLA_local[2],
        #                       attacker_LLA[0], attacker_LLA[1], attacker_LLA[2])
        L_dan = target_distance_local
        t_dan = int(L_dan / V_dan)

        flag_fangan = 0 # 这个是用于提前量方案选择的。2024年，由于是直接进毁伤，所以算提前量的意义其实就没了。
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
        LLA = self.get_LLA(ID,status=self.status)
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
        # 2024年了，今年的这个函数主要用于找周围的房子。一定范围内有房子，就过去，没有，就原地。
        jvli_threshold = 50 # 50米内有房子，就认为可以去一下，不然原地了
        jvli_min = 114514
        index_min = -1
        for i in range(len(self.building_loaction_list)): # 反正就那几个房子，遍历一下完事儿了，没啥好进一步优化的。
            building_single = self.building_loaction_list[i]
            LLA_here[2] = building_single[2]
            jvli_single = self.distance2(LLA_here, building_single)
            if (jvli_single < jvli_min) and (jvli_single < jvli_threshold):
                # 那就是这周围有合适的。给出最近的一个的ID
                index_min = i 

        # 然后看循环完了之后能不能有返回的结果。
        if index_min == -1:
            LLA_jieguo = LLA_here
            shelter_flag = False  # 附近没有什么房子
        else:
            # 那就是真的找到了，那就是可喜又可贺
            LLA_jieguo = self.building_loaction_list[index_min]
            shelter_flag = True # 旁边有个房子，那还是得过去的。

        return LLA_jieguo, shelter_flag

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
 
    def get_n_vector_tan(self,attacker_LLA, center_LLA):
        # 这个就是做个简单的向量运算把切线求出来
        # 先根据当前位置算出切线方向。
        attacker_LLA = np.array(attacker_LLA)
        center_LLA = np.array(center_LLA)
        n_vector_r = attacker_LLA - center_LLA # 末减初，那就是向量了
        n_vector_r[2] = 0 
        n_vector_r = n_vector_r / (np.linalg.norm(n_vector_r)+0.000000001)
        n_vector_z = np.array([0, 0, 1]) # 这个是搞一个竖着的向量，用来求切线。
        n_vector_tan = np.cross(n_vector_r, n_vector_z) # 这个就是切线向量了
        return n_vector_tan # 顺时针逆时针的说法外面再说，这里默认逆时针
    
    def get_state(self, cur_myState, cur_enemyState):
        # 把这些个东西整成能够检索的形式。以及比对是不是有东西被摧毁了
        self.my_state = cur_myState
        self.enemy_state = cur_enemyState
        pass

    def get_status(self):
        # 这个是新加的，用于接大模型
        return self.status , self.detected_state 

    def update_detectinfo(self, detectinfo):
        # 处理一下缓存的探测。2024.一个合理的搞法应该是探测到的都不忘记，然后需要更新就更新。
        # 然后能同步就都同步过去，不能同步的话就用自己能拿到的detectinfo更新。
        # 按说还得有一个机制来实现“不联通的时候探测到的东西在联通了之后能传回来”，不过这个先不慌
        # 好吧,这个并不需要。探测池子里面给到的“上一步”似乎是对的。
        for target_ID in detectinfo:
            for filter_ID in self.weapon_list:
                if filter_ID in target_ID:
                    continue  # 如果探测到的是弹药，那就不要了。

            target_state = {}

            target_state_single = {}
            lon = detectinfo[target_ID]["targetLon"]
            lat = detectinfo[target_ID]["targetLat"]
            if lon==None:
                lon=0
            if lat==None:
                lat=0
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

        # 整个过滤机制，时间太长的探测信息就直接不保存了。被打爆的也不存了。
        list_deleted = []
        for target_ID in self.detected_state2:
            if (self.num - self.detected_state2[target_ID]["this"]["num"]) > 500:
                # 姑且是500帧之前的东西就认为是没用了。
                list_deleted.append(target_ID)
            # 然后被打过且从态势里消失的东西也先不存了。就认为是炸了。
            elif "num_attacked" in self.detected_state2[target_ID]:
                num_attacked = self.detected_state2[target_ID]["num_attacked"]
                if num_attacked>2:
                    # 那就视为被打了，如果此时新鲜态势里没有，就认为是被打爆了。
                    if not(target_ID in detectinfo):
                        # 这个就是被打了。
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
                # prior_list = ["MainBattleTank", "ArmoredTruck", "missile_truck", "Howitzer"]
                prior_list = [ "missile_truck", "MainBattleTank","JammingTruck", "Howitzer", "Infantry"] # 先不打小车，用于调试
            else:
                prior_list = ["missile_truck", "MainBattleTank","JammingTruck", "ArmoredTruck", "WheeledCmobatTruck", "Infantry",  "Howitzer", "Infantry"]
        elif ("ArmoredTruck" in type):
            if self.num < 20:  # 先不打别的，就打防空车。
                prior_list = ["missile_truck", "MainBattleTank"]
            else:
                prior_list = ["missile_truck","JammingTruck", "MainBattleTank", "ArmoredTruck", "Infantry", "missile_truck",
                              "Howitzer"]
        elif ("Howitzer" in type) or ("Infantry" in type):
            prior_list = ["MainBattleTank", "missile_truck", "JammingTruck", "ArmoredTruck", "WheeledCmobatTruck", "Infantry",
                          "Howitzer"]

        elif ("ShipboardCombat_plane" in type):
            prior_list = []
            # 这里面还得详细区分一下，蓝方的主要打红方的榴弹炮，红方的就自由一些
            if "ShipboardCombat_plane1" in type: # 这个type其实输入进来的是attacker ID。
                if self.num % 10 == 0:  # 这个没有CD，手动给它加个CD
                    if self.num < 480:  # 先不打小车，反正打不中。
                        pass
                        # 调试用的。
                        # prior_list = ["missile_truck", "MainBattleTank", "ArmoredTruck", "WheeledCmobatTruck", "missile_truck", "Howitzer", "Infantry"]
                    elif self.num < 1000:
                        prior_list = ["Howitzer"]
                    else:
                        # prior_list = ["Howitzer", "missile_truck", "ArmoredTruck",  "Infantry"]
                        prior_list = ["Howitzer", "MainBattleTank", "ArmoredTruck"]
            elif "ShipboardCombat_plane0" in type:
                # 红方反而可以有啥打啥，不用特别去针对。
                if self.num % 20 == 0:  # 这个没有CD，手动给它加个CD
                    if self.num < 480:
                        prior_list = ["missile_truck", "MainBattleTank", "JammingTruck"]
                        # pass
                    else:
                        prior_list = ["missile_truck", "MainBattleTank", "JammingTruck"]
            else:
                # 容错的，以防万一。
                if self.num % 20 == 0:  # 这个没有CD，手动给它加个CD
                    prior_list = ["missile_truck", "MainBattleTank", "JammingTruck"]


        elif ("Infantry" in type):

            if self.num < 100:  # 先打机械的
                prior_list = ["missile_truck", "MainBattleTank", "ArmoredTruck", "WheeledCmobatTruck"]
            else:
                prior_list = ["missile_truck", "MainBattleTank", "ArmoredTruck", "WheeledCmobatTruck", "missile_truck", "Howitzer", "Infantry", ]

        elif ("missile_truck" in type):
            # 优先打击敌方火力单位好了。
            # 这个也来实现一个“导弹先不慌开火”
            if self.num<2200:
                prior_list = [] 
            else:
                prior_list = ["MainBattleTank",  "missile_truck", "Howitzer", "ArmoredTruck", "Infantry",
                            "WheeledCmobatTruck"]
        elif ("WheeledCmobatTruck" in type):
            # 只能打兵的，那就打兵了。
            # 子弹应该很难消耗完，所以子弹打到车上去了讲道理也不是很有所谓。
            prior_list = ["Infantry", "Truck", "Howitzer", "missile_truck", "MainBattleTank"]
        elif("CruiseMissile" in type):
            # # 统一设定成巡飞弹开始不开火，除非遇到敌方防空，后面快爆炸了就是有什么来什么了。
            if "RedCruiseMissile" in type:
                # 那这个就是红方的，省着点儿炸。
                if "RedCruiseMissile_0" in type:
                    yuzhi = 1200 
                else:
                    yuzhi = 1400
                if self.num < yuzhi: 
                    prior_list = [] # 先探测，先不打
                elif self.num < yuzhi+400:
                    prior_list = ["missile_truck"]
                else:
                    # 有什么打什么了。
                    prior_list = ["missile_truck", "MainBattleTank", "ArmoredTruck", "WheeledCmobatTruck", "missile_truck", "Howitzer", "Infantry"]

            elif "BlueCruiseMissile" in type:
                # 那这个就是蓝方的，就得早点给它炸了
                if "BlueCruiseMissile_0" in type:
                    yuzhi = 800 
                else:
                    yuzhi = 1000

                if self.num < yuzhi:  
                    prior_list = [] # 先探测，先不打
                else:
                    # 有什么打什么了。# 按理说是打不了"JammingTruck"的
                    prior_list = [ "MainBattleTank",  "Howitzer","JammingTruck"]         
            else:
                    prior_list = [ "MainBattleTank",  "Howitzer","JammingTruck"]              
        else:
            # 以防万一
            prior_list = ["missile_truck", "MainBattleTank", "Howitzer", "Infantry", "ArmoredTruck",
                          "WheeledCmobatTruck"]
        return prior_list

    def check_attack_missile_truck(self, weapon_selected, target_ID):
        # 这个是用来监控打死了对面多少的导弹车。
        # 退而求其次，监控对对面导弹车打了多少炮。用这个来估计是不是对。
        # 存个dict，哪个敌方导弹车被打了多少炮。
        if "missile_truck" in target_ID:
            if (weapon_selected == "HighExplosiveShot") or \
                (weapon_selected == "ArmorPiercingShot") or \
                (weapon_selected == "ShortRangeMissile") or \
                (weapon_selected == "RPG"):
                # 只有这几种被认为是打上去有用的。其他子弹啥的就不计入其中了。
                if target_ID in self.missile_truck_attacked:
                    self.missile_truck_attacked[target_ID] = self.missile_truck_attacked[target_ID] + 1
                else:
                    # 稍微容错一点，有的话就+1，没有的话就放那置为1
                    self.missile_truck_attacked[target_ID] =  1
            
            if self.num>1500:
                # 前面要是没打到导弹车，也别憋着了，直接给它拉满。
                self.missile_truck_attacked[target_ID]=114514

        pass
    
    def check_attack_all(self, weapon_selected, target_ID):
        # 干脆所有的都记录了算了
        if "num_attacked" in self.detected_state2[target_ID]:
            self.detected_state2[target_ID]["num_attacked"] = self.detected_state2[target_ID]["num_attacked"] + 1
        else:
            self.detected_state2[target_ID]["num_attacked"] = 1   

    def check_CruiseMissile_ganrao(self, attacker_ID, target_ID):
        # 这个用来check一下，巡飞弹攻击目标是不是在敌方干扰的范围之内。如果是在敌方干扰范围之内就不打了先，如果不是再打。
        # 其实也不安全，因为还可能飞过去的途中就变成在干扰范围内了。比较理想的是一直巡飞，只攻击比较靠近的敌方的东西。
        # 约定：具备攻击条件返回True，不具备就返回False
        flag_target_ganrao = True
        if "CruiseMissile" in attacker_ID:
            # 那就是需要进行check

            # 尝试取出敌方干扰车的坐标。
            flag_detected = False
            self.flag_standingby = False # 这个就先不收别的指令了
            enemy_id_selected = ""
            for enemy_id in self.detected_state2:
                if "Jamm" in enemy_id:
                    flag_detected=True
                    enemy_id_selected = enemy_id
            if flag_detected == True:
                # 那就是对面开着干扰呢，那就check距离
                Jammer_LLA = self.detected_state2[enemy_id_selected]["this"]["LLA"]
                target_LLA = self.detected_state2[target_ID]["this"]["LLA"]
                jvli_target_Jammer = self.distance2(Jammer_LLA,target_LLA)
                if jvli_target_Jammer>2500:
                    # 大于干扰半径的才去A，否则不去A
                    flag_target_ganrao = True
                else:
                    flag_target_ganrao = False
            else:
                # 如果对面没开干扰，那也无事发生
                flag_target_ganrao = True
                pass
        else:
            # 如果不是巡飞弹，那就无事发生。
            flag_target_ganrao = True
            pass

        return flag_target_ganrao    


    def check_zhimiao(self, attacker_ID, target_ID, weapon_selected):
        # 这个用来判断是不是直瞄。然而2024年无所谓直瞄不直瞄了。
        # 确切地说，这个用来封装武器类型和直瞄间瞄是否匹配。匹配就输出true，不匹配就输出false
        # 返回true就可以开火了。
        flag_jieguo = False
        if "Infantry" in target_ID:
            flag_jieguo = True
            return flag_jieguo
        else:
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

    def check_dian(self):
        status = self.status
        flag = False
        for attacker_ID in status:
            if ("DespoilControlPos" in attacker_ID):
                flag = True
                break
        return flag

    def check_edge(self,attacker_ID,d_l=0.004):
        # 输出一个是否接近边界。如果接近边界就想别的办法。
        turn_cd = 70
        attacker_LLA = self.get_LLA(attacker_ID)
        flag_near = False
        if self.abstract_state[attacker_ID]["turn_cd"] == 0:
            if (attacker_LLA[0] < 100.0923 + d_l) or (attacker_LLA[0] > 100.18707 - d_l):
                flag_near = True
                self.abstract_state[attacker_ID]["turn_cd"] = turn_cd
            elif (attacker_LLA[1] < 13.6024 + d_l) or (attacker_LLA[1] > 13.6724 - d_l):
                flag_near = True
                self.abstract_state[attacker_ID]["turn_cd"] = turn_cd
        else:
            # 那就是不符合转的条件，CD减1,最小减少到0
            self.abstract_state[attacker_ID]["turn_cd"] = self.abstract_state[attacker_ID]["turn_cd"]-1
            if self.abstract_state[attacker_ID]["turn_cd"]<0:
                self.abstract_state[attacker_ID]["turn_cd"] = 0 
        return flag_near
    
    def check_distance(self,attacker_ID, d_l = 3000):
        # 输出一个是否远离大部队。
        turn_cd = 70
        attacker_LLA = self.get_LLA(attacker_ID)
        flag_far = False
        if self.abstract_state[attacker_ID]["turn_cd"] == 0:
            # 那就是转向的CD好了，可以转向了.那就要check一下距离了。
            tank_status = self.select_by_type("MainBattleTank")
            xiaoche_status = self.select_by_type("ArmoredTruck")
            che_status = self.select_by_type("WheeledCmobatTruck")
            pao_status = self.select_by_type("Howitzer")
            ganraoche_status = self.select_by_type("JammingTruck") 
            status_ground = tank_status |  xiaoche_status | che_status |  pao_status | ganraoche_status
            # 然后算个平均坐标。
            LLA_average = self.get_LLA_ave(status=status_ground)
            # 然后算个距离。
            jvli = self.distance2(attacker_LLA,LLA_average)
            # 然后检测如果距离超了就转弯，且刷CD
            if jvli > d_l:
                flag_far = True
                self.abstract_state[attacker_ID]["turn_cd"] = turn_cd

            pass
        else:
            # 那就是不符合转的条件，CD减1,最小减少到0
            self.abstract_state[attacker_ID]["turn_cd"] = self.abstract_state[attacker_ID]["turn_cd"]-1
            if self.abstract_state[attacker_ID]["turn_cd"]<0:
                self.abstract_state[attacker_ID]["turn_cd"] = 0 
        
        return flag_far
    
    def __status_filter(self, status):
        # 这个用于滤除奇怪的东西.为了保持兼容，稍微改一下
        status_new = self._status_filter(status,model="me")
        return status_new

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

        # 2024：加一点花样，防御正面的方向，搞成可以选择的
        if "vector_LLA" in kargs:
            vector_LLA = kargs["vector_LLA"]
        else:
            target_LLA = np.array(target_LLA)
            vector_LLA = target_LLA - LLA_average
        
        vector_LLA[2] = 0  # 投影到二维上
        vector_LLA = vector_LLA / np.linalg.norm(vector_LLA)  # 虽然未见得必要,但是还是归一化一下.

        # 然后开始布阵了
        vector_n_LLA = np.array([-1 * vector_LLA[1], vector_LLA[0], 0])  # 生成一个法向量
        # dL = 0.0003  # 别吃三十米的导弹aoe
        dL = 0.0005  # 在此基础上加一点。不要离得太远，太远就不好了

        # 先来个最基本的方方正正的好了,方阵往里面填就是了
        # 增加一些设定，就是根据装备的数量来确定要出几个点。
        ID_list = list(status.keys())
        LLA_list = []
        geshu = len(ID_list)

        if geshu==1:
            p_config = [1,1,0,0] 
        elif geshu<=3:
            p_config = [1,3,1,0] 
        elif geshu<=9: # 还是不太理想，当前这种
            p_config = [3,3,1,1]
        elif geshu<=15:
            p_config = [3,5,2,1] 
        else:
            p_config = [3,7,3,1] 
        
        for j in range(p_config[0]):
            for i in range(p_config[1]):
                d_vector = (-1*p_config[2] + i) * vector_n_LLA + (-1*p_config[3] + j) * vector_LLA
                d_LLA = d_vector * dL
                LLA_single = target_LLA + d_LLA
                LLA_list.append(LLA_single)

        
        # 然后开始往这一堆的点里面填充装备
        for i in range(min(len(status), len(LLA_list))):
            # 写成有序的形式是为了能够保证输入的序列顺序一样,输出的阵型形状就一样.

            attacker_ID = ID_list[i]  # 这里按说得有一个排序机制,体现出排阵型的策略.不过这个可以不用放在这里实现
            target_LLA = LLA_list[i]
            # 2024:这里得根据装备类型改一下，不再所有都是默认的move_and_attack了。
            if "JammingTruck" in attacker_ID:
                # 干扰的就用干扰的。
                self.set_move_and_jammer(attacker_ID, target_LLA, model=1)
                # self.set_move_and_jammer(attacker_ID, target_LLA, model=0)
            else:
                self.set_move_and_attack(attacker_ID, target_LLA)

        # 按理来说这个指令一发,都到位了就能看到阵型了,然后往前A,先到的就隐蔽起来等一下,好像也没有什么不好的.

    def group_A2(self, target_LLA, che_status, bing_status):
        # 这个是步兵和步战车专属的，丑陋可耻但有用。
        # 算了做个容错机制

        che_ID_list = list(che_status.keys())
        bing_ID_list = list(bing_status.keys())
        geshu = min(len(che_status), len(bing_status))

        # 还是整个分散一下的东西。生成一个圆形的阵形
        LLA_list = self.__get_LLA_around(target_LLA, n_R=2, n_theta=3, dR=0.001)
        
        # 检测一下是不是已经去到了，如果已经在那附近了就不触发上下车了。不然就是下车上车下车上车在那傻逼了。
        LLA_bing = self.get_LLA_ave(bing_status)

        jvli = self.distance2(LLA_bing, target_LLA)
        if jvli < 114.514 :
            # 那就是在目标点附近了，就不用触发上下车了
            pass
        else:
            for i in range(geshu):
                self.set_charge_and_xiache(che_ID_list[i], bing_ID_list[i], LLA_list[i])


    def group_A_gai(self, target_LLA, status,**kargs):
        # 这个是改进的group A，每次只A一小段那种，用于长途跋涉。
        
        # 首先读出当前这个group_A_gai实例对应的名字。
        if "name" in kargs:
            name = kargs["name"]
        else:
            name = self.player

        if not(name in self.group_A_gai_config):
            self.group_A_gai_reset(name=name)
        

        if self.group_A_gai_config[name]["flag_end"] == True:
            self.group_A_gai_reset(name=name)
            return  # 跑完了就返回去。

        ave_LLA = self.get_LLA_ave(status)
        dL = self.group_A_gai_config[name]["dL"]
        if self.group_A_gai_config[name]["flag_start"] == False:
            # 那就是这个是第一步，初始化一下这些个状态。
            self.group_A_gai_config[name]["flag_start"] = True
            self.group_A_gai_config[name]["flag_end"] = False
            self.group_A_gai_config[name]["target_LLA"] = np.array(target_LLA)

            dl_vector = target_LLA - ave_LLA
            dl_vector[2] = 0
            dl_vector = dl_vector / np.linalg.norm(dl_vector)
            # 求出方向然后归一化以备后用
            self.group_A_gai_config[name]["dl_vector"] = dl_vector
            # 然后生成一个
            target_LLA_next = ave_LLA + dl_vector * dL
            self.group_A_gai_config[name]["target_LLA_next"] = target_LLA_next
        else:
            target_LLA = self.group_A_gai_config[name]["target_LLA"]
            target_LLA_next = self.group_A_gai_config[name]["target_LLA_next"]
            dl_vector = self.group_A_gai_config[name]["dl_vector"]
            jvli2 = self.distance2(target_LLA_next, ave_LLA)

            if jvli2 < (self.degree_to_m(dL)*5):
            # if jvli2 < 114.514: # 这里的判据取得不好的话会中间停了不动了。
                jvli = self.distance(target_LLA[0], target_LLA[1], target_LLA[2],
                                     ave_LLA[0], ave_LLA[1], ave_LLA[2])

                if abs(jvli - jvli2) < dL * 0.5:
                    # 那就是到了，就得停了完事了
                    self.group_A_gai_config[name]["flag_end"] = True
                else:
                    # 那就是到了一个点了，那就下一个点
                    target_LLA_next = ave_LLA + dl_vector * dL
                    self.group_A_gai_config[name]["target_LLA_next"] = target_LLA_next
                    self.group_A(target_LLA_next, status=status,**kargs)
            else:
                # 那就是没到，那就继续跑呗。
                if self.num % 14 == 0:
                    self.group_A(target_LLA_next, status=status,**kargs)
                pass

        return

    def group_A_gai_reset(self, name="red"):
        # name用来区分不同个数的指令
        # 行吧，还是得整理一下架构。现在这么玩儿，变成红方用了蓝方就不能用了，不是扯淡吗。搞个dict来存好了，加一层。
        group_A_gai_config_defualt = {"target_LLA": [],
                                   "start_LLA": [],
                                   "target_LLA_next": [],
                                   "flag_start": False,
                                   "flag_end": False,
                                   "dL": 0.008,
                                   "dl_vector": []}
        
        self.group_A_gai_config[name] = group_A_gai_config_defualt

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
    
    def check_enemy_direction(self, detected_state2, base_LLA):
        # 这个是“根据输入的态势。判断敌方来的方向”，先不管什么分兵诱敌之类的。
        # 显然，这个需要平滑，不然一跳变都傻逼了。刚好用一下detected_state2里面的两帧数据
        # 输出一个法向量，记录了敌方相对于那个点的进攻方向。
        # 只算这几个种类的地面装备，不然全烂了。
        filter_list = ["MainBattleTank","ArmoredTruck","WheeledCmobatTruck","JammingTruck"] 
        
        # 敌方位置直接求平均了。
        LLA_all = np.zeros((3,))
        base_LLA = np.array(base_LLA)
        num_counted = 0 # 不整花活儿了，直接加起来计数除一下算了。反正没几个，溢出不了。
        for enemy_id in detected_state2:
            flag_is_ground = False
            for filter_str in filter_list:
                if filter_str in enemy_id:
                    flag_is_ground = True
            if flag_is_ground:
                this_LLA = detected_state2[enemy_id]["this"]["LLA"]
                # 如果还存了上一步的，就把上一步的也纳入计算。没有的话就自己把自己再来一遍。
                try:
                    last_LLA = detected_state2[enemy_id]["last"]["LLA"]
                except:
                    last_LLA = this_LLA
                LLA_all[0] = LLA_all[0] + (this_LLA[0] + last_LLA[0]) / 2 
                LLA_all[1] = LLA_all[1] + (this_LLA[1] + last_LLA[1]) / 2
                num_counted = num_counted + 1
        
        # 然后把平均值算出来。
        if num_counted==0:
            LLA_all = np.zeros((3,))
        else:
            LLA_all = LLA_all / num_counted 

        # 然后求个向量。
        n_fangxiang = base_LLA - LLA_all # 由于是敌方来的方向，所以是末减初
        n_fangxiang = n_fangxiang / np.linalg.norm(n_fangxiang)

        return n_fangxiang, LLA_all 

    def check_enemy_group(self, detected_state2, R_threshold=1500):
        # 这个做个聚类，求出detected_state2的子集，返回一个列表，以及一个“聚合度指标”，来衡量是不是一起来的。
        # 但是如果上什么kmeans那些的话开销会比较大，还需要思想更滑坡然后更可控的解决方案。
        # 直接用3个城市的坐标作为聚类中心，判断各个单位周围敌方坐标的数量，再来个方差。但是似乎也就比kmeans好点有限。

        # if R_threshold>0.2:
        #     # 那就说明给进来的是米的量纲，那就化成经纬度。
        #     R_threshold = self.m_to_degree(R_threshold)
        # else:
        #     # 那就认为输入进来的是经纬度的那个量纲，那就直接来
        #     pass

        # 对前三个房子周围的敌人来做聚类。

        n_type = 3 

        result_state_list = [] 
        for i in range(n_type):
            result_state_list.append({})
        number_list = np.zeros((n_type,))

        detected_state2 = self._status_filter(detected_state2,model="me")

        for enemy_single in detected_state2:
            enemy_single_LLA = detected_state2[enemy_single]["this"]["LLA"]
            for i in range(n_type):
                building_LLA = self.building_loaction_list[i]
                # enemy_single_LLA[2]=0 # 是不是要来这个，恐怕有待商榷。加了这个可能会被飞机影响节奏
                jvli = self.distance2(enemy_single_LLA, building_LLA)
                if jvli < R_threshold*114514:
                    # 那就说明是要归在这一类里面 
                    result_state_list[i][enemy_single] = detected_state2[enemy_single]
                    number_list[i] = number_list[i] + 1
                    break
        
        # 循环完了就意思是分类好了，那就计数咯
        # 计数完了感觉得归一化一下再来。
        number_list = number_list / np.sum(number_list)
        variance = np.var(number_list) / 0.22222222222222222222 # 这个也是给它归一化到[0,1]之间了大致

        # 还得再返回一个“第几个房子附近的兵最多”的index。方便后面使用。
        index = np.where(number_list == max(number_list))
        index = int(index[0][0]) #numpy就是事儿多

        return  result_state_list, variance, index

    def check_enemy_direction2(self,detected_state2,base_LLA,**kargs):
        # 这个是一开始准备用于红方的，返回的是“是否探到了足够的数量的敌方地面单位”，以及“敌方主力往什么方向去了”
        filter_list = ["MainBattleTank","ArmoredTruck","WheeledCmobatTruck","JammingTruck","Howitzer_C100"] 
        LLA_all = np.zeros((3,))
        num_counted = 0 
        if "num_threshold" in kargs:
            num_threshold = kargs["num_threshold"]
        else:
            num_threshold = 4 

        for enemy_id in detected_state2:
            flag_is_ground = False
            for filter_str in filter_list:
                if filter_str in enemy_id:
                    flag_is_ground = True
            if flag_is_ground:
                this_LLA = detected_state2[enemy_id]["this"]["LLA"]
                # 如果还存了上一步的，就把上一步的也纳入计算。没有的话就自己把自己再来一遍。
                try:
                    last_LLA = detected_state2[enemy_id]["last"]["LLA"]
                except:
                    last_LLA = this_LLA
                LLA_all[0] = LLA_all[0] + (this_LLA[0] + last_LLA[0]) / 2 
                LLA_all[1] = LLA_all[1] + (this_LLA[1] + last_LLA[1]) / 2
                num_counted = num_counted + 1
        
        # 然后把平均值算出来。
        if num_counted==0:
            LLA_all = np.zeros((3,))
        else:
            LLA_all = LLA_all / num_counted 
        # 看探测到的数量够不够，够了就然后对比，对比第一个L。
        flag_detected = False
        if num_counted>num_threshold:
            flag_detected = True
        
        enemy_direction = "none"
        # 然后就是处理一下返回值，红蓝方的返回值不一样的。
        if self.player == "red":
            if LLA_all[0]>base_LLA[0]:
                # 那就说明平均出来是在地图偏右边的地方，
                # 需要的话还可以加一点阈值，比如足够右才算右
                enemy_direction = "right" 
            else:
                enemy_direction = "left"
        elif self.player == "blue":
            if LLA_all[0]<base_LLA[0][0]:
                # 那就是最左边
                enemy_direction = "left"
            elif LLA_all[0]<base_LLA[1][0]:
                enemy_direction = "center"
            elif LLA_all[0]>base_LLA[1][0]:
                enemy_direction = "right"
                
        # 然后看返回值
        return flag_detected, enemy_direction
    
    def check_enemy_direction_dummy(self,detected_state2,base_LLA,**kargs):
        # 这个是调试用的简单版的，用于调试和简化战术。
        # 后期可以发展成针对性的说法。

        # 先来个最简单版本的“到特定步数就输出”
        if self.num == 200:
            flag_detected = True
            enemy_direction = "right" 
        else:
            flag_detected = False
            enemy_direction = "right"
        
        return flag_detected, enemy_direction


    # 后面是服务于大模型的
    def set_commands(self, command_list:list):
        # print("set_commands: unfinished yet")
        # 首先把这些个command加入到queue里面去。增加一个键值对，当前时间。
        for comand_single in command_list:
            comand_single["step_num"] = self.num
            self.commands_queue.put(comand_single)
        
        # 然后开始执行，具体的逻辑还得想想。
        # 拿出第一个，如果是这一步的，就给它执行了，如果不是，就结束退出。

        for i in range(114514): # 原则上这里应该是个while，但是保险起见防止死循环。
            if len(self.commands_queue.queue)==0:
                return # 没有什么命令，直接溜了溜了。
        
            # 看一下第一个
            comand_single = self.commands_queue.queue[0]
            if comand_single["step_num"] <= self.num:
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
                        self.set_charge_and_xiache(obj_id, bing_id, target_LLA)
            elif "Infantry" in obj_id:
                # 步兵的话就是前面一定步数不做行动，后面再做行动。或者说，正在等上车的话就不做行动。
                for i in range(5): # 丑陋的字符串拼接操作，毫无通用性可言，鉴定为拉。
                    if str(i) in obj_id:
                        # 说明对应的是这个车。
                        che_id = "WheeledCmobatTruck" + "_ZB100_"+str(i)
                        try:
                            if self.abstract_state[che_id]["abstract_state"] == "charge_and_xiache":
                                self.set_none(obj_id)
                            else:
                                # 那就是说现在不需要上下车，那就冲。
                                self.set_move_and_attack(obj_id, target_LLA)
                        except:
                            # 这里这个异常处理是为了防止复盘的时候跑出来的结果由于随机性导致不一样导致复盘命令变化
                            pass 
                    else:
                        # 说明对应的不是这个车，那就无事发生。
                        pass 
            else:
                # 除了车和步兵以外的情况，那就走呗，move。            
                self.set_move_and_attack(obj_id, target_LLA)             
        elif comand_single["type"] == "stop":
            self.set_open_fire(comand_single["obj_id"])
            # self.set_stop(comand_single["obj_id"])
            pass 
        elif comand_single["type"] == "off_board":
            # 这里要投机取巧了，不想新加抽象状态了，而是在当前抽象状态的基础上直接改变量。
            if "WheeledCmobatTruck" in obj_id:
                target_LLA = self.__get_LLA(obj_id)
                if "next" in self.abstract_state[obj_id]:
                    if self.abstract_state[obj_id]["next"]["abstract_state"] == "charge_and_xiache":
                        # 另一种情况。其实这个应该是更广泛的情况。它在走，但是charge_and_xiache是在next里面。
                        self.__finish_abstract_state(obj_id)
                if self.abstract_state[obj_id]["abstract_state"] == "charge_and_xiache":
                    # 改抽象状态，让它觉得现在可以下车了，从而实现下车。
                    self.abstract_state[obj_id]["target_LLA"] = target_LLA
                    self.abstract_state[obj_id]["flag_state"] = 3
                
        else:
            raise Exception("undefined comand type in set_commands_single, G.") 
 
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
    
    def get_nearest_bridge(self, target_LLA):
        # 这个是输出离指定位置最近的一个桥的位置，预备是用来守桥的

        jvli_list = [] 
        
        for LLA_single in self.bridge_location_list:
            jvli_single = self.distance(target_LLA[0], target_LLA[1], target_LLA[2], LLA_single[0], LLA_single[1], LLA_single[2])
            jvli_list.append(jvli_single)


        # 然后找最近的.
        if len(jvli_list)>0:
            jvli_nearest = min(jvli_list)
            index_min = jvli_list.index(jvli_nearest)
            bridge_LLA = self.bridge_location_list[index_min]
        else:
            jvli_nearest = 1145141919
        
        return bridge_LLA,jvli_nearest