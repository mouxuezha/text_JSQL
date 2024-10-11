# 这个用来实现“JSON态势转化成文本态势”，以及约定一些命令的信息

# 需要约定一下命令格式了。
import math
import json
class text_transfer(object):
    def __init__(self) -> None:
        self.command_type_list = ["move", "stop", "off_board"]
        self.type_transfer = type_transfer()
        self.num_commands = [0,0] # 第一个是转化成功的commands，第二个是转化失败的commands 
        self.ed_lat,  self.ed_lon =  39.70, 2.68984
        self.tar_lat, self.tar_lon = 39.7600, 2.7100

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



    def status_to_text(self, status):
        # print("status_to_text unfinished yet,return a demo")
        status_str = ""
        for obj_id in list(status.keys()):
            unit_status = status[obj_id]
            lon = round(unit_status["VehicleState"]["lon"], 5) 
            lat = round(unit_status["VehicleState"]["lat"], 5)
            alt = round(unit_status["VehicleState"]["alt"], 5)
            unit_type_zhongwen = self.type_transfer.unit_type_transfer(unit_status["UnitType"])
            if unit_type_zhongwen == "其他":
                # 什么BMC3那些就别拿进来了
                continue
            else:
                status_str +="红方obj_id为"+str(obj_id)+"的"
                status_str += f"{unit_type_zhongwen}位置在({lon},{lat})处 \n"
        return status_str
    
    def detected_to_text(self, detected_state):
        # 这里面的探测到的数据结构还不太一样，所以需要另外开一个函数来实现
        detected_str = ""
        for obj_id in list(detected_state.keys()):
            detected_status = detected_state[obj_id]
            lon = round(detected_status["targetLon"], 5)
            lat = round(detected_status["targetLat"], 5)
            alt = round(detected_status["targetAlt"], 5)
            detected_type_zhongwen = self.type_transfer.unit_type_transfer(detected_status["unitType"])
            if detected_type_zhongwen == "其他":
                continue
            else:
                detected_str +="蓝方obj_id为"+str(obj_id)+"的"
                detected_str += f"{detected_type_zhongwen}位置在({lon},{lat})处 \n"
        print("text_transfer detected_to_text:" + detected_str)
        return detected_str
        pass 

    #  把态势翻译成人话
    def turn_taishi_to_renhua(self, status, detected_state):
        our_status = dict()
        for obj_id in list(status.keys()):
            unit_status = status[obj_id]
            lon = round(unit_status["VehicleState"]["lon"], 5) 
            lat = round(unit_status["VehicleState"]["lat"], 5)
            alt = round(unit_status["VehicleState"]["alt"], 5)
            unit_type_zhongwen = self.type_transfer.unit_type_transfer(unit_status["UnitType"])
            if unit_type_zhongwen == "其他":
                # 什么BMC3那些就别拿进来了
                continue
            else:
                our_status[obj_id] = {"type": unit_type_zhongwen, "lon": lon, "lat":lat, "alt": alt}
        detect_state = dict()
        for obj_id in list(detected_state.keys()):
            detected_status = detected_state[obj_id]
            lon = detected_status["targetLon"]
            lat = detected_status["targetLat"]
            alt = detected_status["targetAlt"]
            detected_type_zhongwen = self.type_transfer.unit_type_transfer(detected_status["unitType"])
            if detected_type_zhongwen == "其他":
                continue
            else:
                detect_state[obj_id] = {"type": detected_type_zhongwen, "lon":lon, "lat":lat, "alt":alt}
        # 怎么翻译成人话  从哪些角度翻译
        # 这几个点吧  主力位置 敌方集群向哪个方向移动  是主力还是啥  意图可能是啥  都有啥装备  我方大概需要怎么配合
        keypoints = None
        enemy_tank_id = self.select_by_type(detect_state, "坦克")
        enemy_tank_lat_avg, enemy_tank_lon_avg  = self.get_avg_pos(enemy_tank_id, detect_state)
        our_tank_id = self.select_by_type(our_status, "坦克")
        our_tank_lat_avg, our_tank_lon_avg = self.get_avg_pos(our_tank_id, our_status)
        enemy_direct = self.relative_pos(our_tank_lat_avg, our_tank_lon_avg, enemy_tank_lat_avg, enemy_tank_lon_avg)
        group_dis = self.distance(enemy_tank_lon_avg, enemy_tank_lat_avg, 0, our_tank_lon_avg, our_tank_lat_avg, 0)
        enemy_in_range_dict = self.find_nearest_enemy(our_tank_lat_avg, our_tank_lon_avg, detect_state, 3000)
        enemy_in_range_renhua =  self.turn_dict_to_renhua(enemy_in_range_dict)
        # messages = f"""
        #     当前探测到对方主力装备位于我方装备的{enemy_direct}方向，我方平均距离为{group_dis} , 敌方在我方射程范围内的装备有 {enemy_in_range_renhua}, 
        # """
        messages = f"探测到敌方在{enemy_direct}方向，平均距离" + str(round(group_dis,1))
        if len(enemy_in_range_renhua)>0:
            messages = messages + ", 射程内敌人有" +str(enemy_in_range_renhua)+","
        if self.check_enemy_closer_to_target(enemy_tank_lon_avg, enemy_tank_lat_avg):
            left_time = self.distance(enemy_tank_lon_avg, enemy_tank_lat_avg, 0, self.tar_lon, self.tar_lat, 0)/20
            left_time = int(left_time)
            messages += f" 敌预计 {left_time}后到达夺控点" 
        return messages 
    # 加一个用来判断是不是靠近夺控点的方法
    def check_enemy_closer_to_target(self, elon, elat):
        std_dis = self.distance(self.ed_lon, self.ed_lat,0,  self.tar_lon, self.tar_lat, 0)
        cur_dis = self.distance(self.tar_lon, self.tar_lat, 0, elon, elat, 0)
        if std_dis > cur_dis:
            return True
        return False
    def select_by_type(self, status, type = "坦克"):
        return [ obj_id for obj_id , values_ in status.items() if type in values_["type"]]
    
    def find_nearest_enemy(self, our_lat, our_lon, detect_status, range = 2500):
        detect_id_list = [_id for _id in detect_status.keys() if self.distance( our_lat, our_lon, 0, detect_status[_id]["lat"], detect_status[_id]["lon"] ,0 ) < range]
        return self.generate_calculate_unit(detect_id_list, detect_status)
    
    def turn_dict_to_renhua(self, cal_detect_dict):
        renhua = """"""
        for _t, _num in cal_detect_dict.items():
            renhua = renhua +  _t +" 数量为 " + str(_num) + " "

        return renhua

    def get_avg_pos(self, idlist, status):
        if len(idlist) == 0:
            return 0, 0
        avg_lat =  sum([status[obj_id]["lat"] for obj_id in idlist])/ len(idlist)
        avg_lon =  sum([status[obj_id]["lon"] for obj_id in idlist])/ len(idlist)
        return avg_lat, avg_lon
    
    def generate_calculate_unit(self, idlist, estatus):
        cal = dict()
        for  _id  in  idlist:
            _val = estatus[_id]
            if _val["type"] not in cal:
                cal[ _val["type"] ] = 1
            else:
                cal[ _val["type"] ] += 1
        
        return cal

    def relative_pos(self, olat, olon, elat, elon):   # 需要优雅一点的写法 
        rdir =  ""
        if  olon > elon :
            rdir +=  "西"
        elif olon < elon:
            rdir +=  "东"
        if olat > elat:
            rdir += "南"
        elif olat < elat:
            rdir += "北"
        return rdir 


    #@szh 0607 将我方装备信息转化为JSON 发送给LLM
    def status_to_text_tojson(self, status):
        print("status_to_text unfinished yet,return a demo")
        status_str = ""
        our_status = dict()
        for obj_id in list(status.keys()):
            unit_status = status[obj_id]
            lon = unit_status["VehicleState"]["lon"]
            lat = unit_status["VehicleState"]["lat"]
            alt = unit_status["VehicleState"]["alt"]
            unit_type_zhongwen = self.type_transfer.unit_type_transfer(unit_status["UnitType"])
            if unit_type_zhongwen == "其他":
                # 什么BMC3那些就别拿进来了
                continue
            else:
                # status_str +="我方obj_id为"+str(obj_id)+"的"
                # status_str += f"{unit_type_zhongwen}位置在({lon},{lat})处 \n"
                our_status[obj_id] = {"type": unit_type_zhongwen, "lon": lon, "lat":lat, "alt": alt}
        our_status_json = json.dumps(our_status)      
        return our_status_json
    
    #@szh 0607 将detect 信息转化为json
    def detected_to_text_tojson(self, detected_state):
        # 这里面的探测到的数据结构还不太一样，所以需要另外开一个函数来实现
        detected_str = ""
        detect_state = dict()
        for obj_id in list(detected_state.keys()):
            detected_status = detected_state[obj_id]
            lon = detected_status["targetLon"]
            lat = detected_status["targetLat"]
            alt = detected_status["targetAlt"]
            
            detected_type_zhongwen = self.type_transfer.unit_type_transfer(detected_status["unitType"])
            if detected_type_zhongwen == "其他":
                continue
            else:
                # detected_str +="敌方obj_id为"+str(obj_id)+"的"
                # detected_str += f"{detected_type_zhongwen}位置在({lon},{lat})处 \n"
                detect_state[obj_id] = {"type": detected_type_zhongwen, "lon":lon, "lat":lat, "alt":alt}
        detect_json = json.dumps(detect_state)
        return detect_json
        pass 



    def text_to_commands(self, text:str):
        
        commands = []
        for command_type in self.command_type_list:
            if command_type == "move":
                index_list = self.find_all_str(text, command_type)
                for i in range(len(index_list)):
                    sub_str = text[index_list[i]:-1]
                    try:
                        x = float(self.cut_from_str(sub_str, "x=", ","))
                        y = float(self.cut_from_str(sub_str, "y=", "]"))
                        obj_id = self.cut_from_str(sub_str, "obj_id=", ",")
                        command_single = {"type": command_type, "obj_id": obj_id, "x": x, "y": y}
                        commands.append(command_single)
                        self.num_commands[0] += 1
                    except:
                        self.num_commands[1] += 1
                        print("G in one move command")
            elif command_type == "stop":
                index_list = self.find_all_str(text, command_type)
                for i in range(len(index_list)):
                    sub_str = text[index_list[i]:-1]
                    try:
                        obj_id = self.cut_from_str(sub_str, "obj_id=", "]")
                        command_single = {"type": command_type, "obj_id": obj_id}
                        commands.append(command_single)
                        self.num_commands[0] += 1 
                    except:
                        self.num_commands[1] += 1
                        print("G in one stop command")
            # elif command_type == "off_board":
            #     index_list = self.find_all_str(text, command_type)
            #     for i in range(len(index_list)):
            #         sub_str = text[index_list[i]:-1]
            #         try:
            #             obj_id = self.cut_from_str(sub_str, "obj_id=", "]")
            #             command_single = {"type": command_type, "obj_id": obj_id}
            #             commands.append(command_single)
            #         except:
            #             print("G in one off_board command")   
        
        # 偷个懒，如果有下车，就让下车的覆盖别的指令好了。另开一个循环，即可。
        # 丑陋但是有用。
        for command_type in self.command_type_list:    
            if command_type == "off_board":
                index_list = self.find_all_str(text, command_type)
                for i in range(len(index_list)):
                    sub_str = text[index_list[i]:-1]
                    try:
                        obj_id = self.cut_from_str(sub_str, "obj_id=", "]")
                        command_single = {"type": command_type, "obj_id": obj_id}
                        commands.append(command_single)
                        self.num_commands[0] += 1
                    except:
                        self.num_commands[1] += 1
                        print("G in one off_board command")      

        print("text_to_commands: valid commands number: "+str(len(commands)))      
        return commands
    
    def get_initial_prompt(self):
        print("get_initial_prompt unfinished yet,return a demo")
        initial_prompt = "请作为兵棋推演游戏的玩家，设想一个陆战作战场景，我方为红方，拥有坦克、步兵战车、自行迫榴炮、无人突击车和无人机、导弹发射车等装备，步兵下车后作战，我方需要攻取位于经纬度坐标(2.7100,39.7600)的夺控点，要将陆战装备移动到夺控点处并消灭夺控点附近敌人，地图范围为经度2.6000到2.8000，纬度范围为39.6500到39.8500，导弹发射车不能机动。在每一步，我将告诉你敌我态势和其他信息，并由你来尝试生成作战指令。"
        # 还需要一些描述地图的prompt
        initial_prompt = initial_prompt + "地图西北方向为海洋，其余部分为陆地。陆地中间部分为山区，装备单位经过山区会由于坡度地形因素，导致行进速度减慢，夺控点周围是一片平原。"
        return initial_prompt
    
    
    


    def get_order_guize(self):
        # 这里面是给大模型设定的规则的格式。
        order_guize = "请按照以下格式给出作战指令。进攻指令：[move, obj_id , x=int, y=int], 如坦克mbt_1进攻坐标为(2.7100, 39.7600)，则指令为[move, obj_id=mbt_1, x=2.7100, y=39.7600] \n 停止指令：[stop, obj_id], 如坦克mbt_1停止当前行动,则指令为[stop, obj_id=mbt_1]。步兵下车指令: [off_board, obj_id],如步战车ifv_1内步兵立刻下车,则指令为[off_board, obj_id=ifv_1]"
        return order_guize
    
    def find_all_str(self, text:str, sub_str:str):
        index_list = [] 
        index = text.find(sub_str)
        while index != -1:
            index_list.append(index)
            index = text.find(sub_str, index + 1)
        
        return index_list
    
    def cut_from_str(self, text:str, str_qian:str, str_hou:str):
        # 需要把数字从字符串中抠出来
        # 先找到数字的起始位置
        index_qian = text.find(str_qian)
        sub_str = text[index_qian+len(str_qian):]
        index_hou = sub_str.find(str_hou)
        # index_hou = text.find(str_hou)
        number_str = sub_str[0:index_hou]
        # number_float = float(number_str)
        return number_str
    
    def get_num_commands(self):
        # 这个算是结果处理，用来看有多少
        str_buffer = "成功识别指令{}个，识别失败{}个。".format(self.num_commands[0], self.num_commands[1])
        str_buffer = str_buffer + "\n识别成功率：" + str(self.num_commands[0]/(self.num_commands[0]+self.num_commands[1]))
        
        print(str_buffer)
        return str_buffer

class type_transfer(object):
    # 这个是用来把抽象的装备类型化简一下的，搞成中文的。
    def __init__(self):
        self.unit_type_dict = {
            'ArmoredTruck': '无人战车' , 
            'Howitzer' : '自行迫榴炮', 
            'infantry': '步兵',
            'MainBattleTank' : '坦克',
            'ShipboardCombat_plane' : '无人机',
            'WheeledCmobatTruck':'步战车', 
            'missile_truck' : '导弹发射车',
        }
    def unit_type_transfer(self, unit_type:str):
        for key in list(self.unit_type_dict.keys()):
            if key in unit_type:
                unit_type_zhongwen = self.unit_type_dict[key]
                break
            else:
                unit_type_zhongwen = "其他"
        return unit_type_zhongwen

#@ szh 0605 先写几个prompt 试一下 
# 目前想的几个点 
# 1 可以做成多轮对话的 看看效果  也就是加一个memory去存  
# 2 对话要带帧数
# 3 后面可以设置配置文件，并读取配置文件来 
# 4 最好是得引导LLM 一步一步来 
# from langchain_community.llms import HuggingFaceHub
# model = HuggingFaceHub(repo_id = "")

# 以qianfan为例 写functioncall
import qianfan
import re


class PromptJSQL:
    def __init__(self):  


        #  以下这些只发送给LLM 一次
        role_template = """
        你是一个兵棋推演游戏的玩家，设想一个陆战作战场景，我方为红方，拥有坦克、步兵战车、自行迫榴炮和无人机等装备。这次陆战推演场景一共有{self.total_num}步，
        在每一步，我将告诉你敌我态势和地图相关信息，并由你来尝试生成作战指令。
        """ 
        cot_template = """
            作为一个兵棋推演的红方玩家，我们的目标是在夺取蓝方防守的夺控点，并利用我方装备尽可能攻击蓝方算子。我们知道夺控点的坐标。
            1.你需要清楚我方装备的当前位置，以及当前的推演帧
            2.你可以得到敌方装备的位置信息以及我方装备的位置信息，以及地图信息。
            3.基于这些信息，你需要去判断我方装备需要执行哪些动作，这些动作包括集结、移动和开火。
            再次强调一下，我们的目标是夺取夺控点，也就是指挥我方装备机动到夺控点所在的坐标。 
        """
        
        # 加入态势的垂直知识模板
        prompt_taishi_explain = {
            "detected_status": """
                 detected_status 表示探测到的敌方装备的信息
                 以JSON形式给你提供当前的敌方装备的类型和位置信息如下: __DETECTED_STATUS__ \n\n , 对前面的JSON关键字的含义解释如下: __DETECTED_STATUS_EXPLAIN__
                 需要你分析判断。
            """,
            "our_status": """
                 our_status 表示我方装备的信息
                 以JSON形式给你提供当前的我方装备的类型和位置信息: __OUR_STATUS__ \n\n ,对前面的JSON关键字的含义解释如下: __OUR_STATUS_EXPLAIN__ \n\n, 
                 需要你分析判断。
            """
        }
        prompt_taishi = {
            "detected_status": """
                 detected_status 表示探测到的敌方装备的信息
                 以JSON形式给你提供当前的敌方装备的类型和位置信息如下: __DETECTED_STATUS__ \n\n 
            """,
            "our_status": """
                 our_status 表示我方装备的信息
                 以JSON形式给你提供当前的我方装备的类型和位置信息: __OUR_STATUS__ \n\n 
            """
        }
        # 提供一些地图的背景知识E
        prompt_map_background = """
        \n\n
            地图的边界坐标为（2.60E, 39.85N）、(2.80E, 39.85N)、 (2.60E, 39.65N)、 (2.80E,39.65N) 我方（红方）的初始部署坐标为{self.our_deploy_point},敌方（蓝方）的初始部署坐标为{self.enemy_deploy_point}
            简单描述一下地图，地图西北方向为海洋，其余部分为陆地。陆地中间部分为山区，装备单位经过山区会由于坡度地形因素，导致行进速度减慢，
            夺控点周围是一片平原。
        \n\n
        """
        
        # 提供一些基础知识的背景 例如 装备的武力值 
        prompt_background = """
        \n\n
            这里给出兵棋推演中的一些基本背景信息，包括装备编成、装备火力值、装备防御值、装备机动速度、装备射程等。你可以认为红蓝双方相同类型的装备具有相同的火力值、射程等参数。例如，红方坦克的射程为2500m，那么可以认为蓝方坦克的射程也为2500m。
            火力值反映了装备对敌方装备的打击毁伤能力，火力值越大，毁伤能力越强，数值表示相对大小。 装备防御值反映了装备对敌方攻击的防御能力，防御值越大，防御能力越强。
            先说明装备编成，本次推演中，我方作为红方，初始时拥有2个步兵班、4辆坦克、2辆无人突击车、一架无人机。 敌方作为蓝方，初始时具有4辆装甲车、4个步兵班、4辆装甲车，一架无人机。
            下面给出各装备的火力值，坦克有穿甲弹和高爆弹，火力值为150。 步战车配备有机枪，火力值为50。 步兵班配备火箭炮，火力值为100。无人机作为侦察装备，配备4枚空对地，火力值为80。无人突击车配备两枚RPG，火力值为80
            下面给出各类型装备的机动速度，坦克机动速度为58km/h、装甲车机动速度为72km/h，步兵班机动速度为10km/h，无人突击车机动速度为108km/h,无人机速度为198km/h。
            下面给出各类型装备的防御值，数值为相对大小。坦克防御值为200，步兵班为140， 无人突击车为80， 装甲车为80，无人机为80。请注意，无人机为空中装备。
            下面给出各类型装备的射程，坦克射程为2500m， 装甲车为1000m，步兵班为1000m，无人突击车为2500m， 无人机为4000m
            在本次推演中，你不需要考虑装备的配弹量和剩余弹量。
        \n\n
        """

        prompt_detect_status_explain = """
        \n\n
           在前面的JSON中，每个key表示探测到的敌方单位的ID，type 表示敌方装备类型， lat、lon、alt,分别表示敌方装备当前所在的经度纬度和高度。你可以根据敌方装备类型和位置信息去判断敌方的行动计划并选择自身行动，估计下一次该敌方装备出现的位置。
           在自身动作选择上，你可以根据敌方装备类型和附近我方装备的情况去分析。例如，你可以通过当前敌方装备和我方装备的位置信息（lat、lon、alt），计算出敌方算子到我方算子的距离，如果在我方武器射程内，则可以向敌方算子开火射击。
           再如，你可以通过敌方装备的类型和位置分布，推断出敌方装备的火力值和防御值，与当前我方装备进行比较，判断是否向前发动进攻还是向后撤退或者是进行迂回配合等作战行动。
        \n\n
         """
        prompt_our_status_explain = """
        \n\n
          在前面的JSON中，每个key表示探测到的我方单位的ID，type 表示敌方装备类型， lat、lon、alt,分别表示敌方装备当前所在的经度纬度和高度。你可以根据敌方装备类型和位置信息去判断敌方的行动计划并选择自身行动，估计下一次该敌方装备出现的位置。
           在自身动作选择上，你可以根据敌方装备类型和附近我方装备的情况去分析。例如，你可以通过当前敌方装备和我方装备的位置信息（lat、lon、alt），计算出敌方算子到我方算子的距离，如果在我方武器射程内，则可以向敌方算子开火射击。
           再如，你可以通过敌方装备的类型和位置分布，推断出敌方装备的火力值和防御值，与当前我方装备进行比较，判断是否向前发动进攻还是向后撤退或者是进行迂回等作战行动。
        \n\n
        """
        prompt_action_explain = """
        \n\n
            - 机动指令(move): [move, obj_id, act] ， 表示我方装备obj_id, 开始机动，方向：<前进>/<后退>/<向左迂回>/<向右迂回>
            - 开火指令(fire): [fire, obj_id] ，表示我方装备obj_id 用武器开火，打击敌方最近的装备。
            - 停止指令(stop): [stop, obj_id] ，表示我方装备obj_id 停止机动。
            - 集结指令(gather): [gather, obj_id, obj_id2] 表示我方装备obj_id1, obj_id2 向同一位置进发。
        \n\n
        """

        output_format = """
        \n\n
        基于敌我双方的态势信息，选择一定的策略，并按以下形式输出
        1.  **当前阶段**： 当前是第{self.num}帧，处在[推演阶段]，其中[推演阶段]的值为以下之一： <早期阶段>，<中期阶段>， <后期阶段>
        2.  **红方（我方）策略**： [总体策略] ，其中[总体策略]的类型为以下之一：<向夺控点前进>、<远离敌方装备后退>、<向敌方左侧迂回>、<向敌方右侧迂回>
        3.  **红方（我方）行动**： 对于我方每个装备单位，给出相应的行动指令，行动指令包括以下一种或者几种(冒号后为输出格式)：
            - 机动指令(move): [move, obj_id, act] ， 其中obj_id 为string 类型，取值范围： 我方单位的ID； act为string类型，取值范围： <前进>，<后退>, <向左迂回>,<向右迂回>
            - 开火指令(fire): [fire, obj_id] ，其中obj_id 为string 类型，取值范围： 我方单位的ID；
            - 停止指令(stop): [stop, obj_id] ，其中obj_id 为string 类型，取值范围： 我方单位的ID；
            - 集结指令(gather): [gather, obj_id, obj_id2, obj_id3],其中obj_id、obj_id2为string 类型，取值范围： 我方单位的ID；
            请按上述格式输出指令，不能输出值为null。
        4.  **态势分析**： 给出我方下一步采用什么策略。
        \n\n
        """
        
        # 这部分是给出一个思考过程的例子
        
        thinking_examples = """
            下面是一个推演决策过程的例子，你需要学习这个例子中的从态势中获取关键信息来进行对我方装备的行动做出决策的过程。之后的推演中会给你发送当前态势，需要你自己推理出合理的决策。
            首先，读取
        
        """

        # 这部分是给输入的例子
        input_example1 = """

        

        """


        # 这部分是给输出指令结果的例子
        output_example1 = """
        \n\n
        1.  **当前阶段**： 当前是第300帧，处在早期阶段
        2.  **红方（我方）策略**： [向夺控点前进] 
        3.  **红方（我方）行动**： 
                [move, ArmoredTruck_ZTL100_0, 前进]
                [move, ArmoredTruck_ZTL100_1, 前进]
                [fire, MainBattleTank_ZTZ100_0]
                [fire, MainBattleTank_ZTZ100_1]
                [move, MainBattleTank_ZTZ100_1, 前进]
                [move, MainBattleTank_ZTZ100_2, 前进]
                [stop, MainBattleTank_ZTZ100_3]
                [move, WheeledCmobatTruck_ZB100_0, 向右迂回]
                [move, WheeledCmobatTruck_ZB100_1, 向左迂回]
                [gather, Infantry0, Infantry1 ]
        4.  **态势分析**： 当前敌方距离夺控点比我方更近，且处在早期阶段，在总体策略上选择向夺控点前进，ArmoredTruck_ZTL100_0、ArmoredTruck_ZTL100_1 类型为无人突击车，速度较快，可以向夺控点进发；
        MainBattleTank_ZTZ100_0 、MainBattleTank_ZTZ100_1 坦克火力比较强，向夺控点进发同时向敌方开火；探测到WheeledCmobatTruck_ZB100_0、WheeledCmobatTruck_ZB100_1 前方有敌方装备，
        由于类型为装甲车防御值较低，需要避开敌方装备，因此选择向左迂回和向右迂回动作。
        \n\n
        """

        # 例子 如何判断并输出集结指令  例如 tank1  tank2  集结到目标位置x
        strategy_examples_gathering = """
                
        
        """
        
        strategy_examples_move = """

        
        """

        strategy_examples_openfire = """


        """

        self.chatcount = 0   # 用来控制对话轮数 
        self.text_transfer_class = text_transfer()
        # 这个prompt template 需要修改 
        self.total_num = 3000
        self.num = 0 
        # 敌我双方部署点信息
        self.our_deploy_point = None
        self.enemy_deploy_point = None
        self.prompt_template = f"{instruction}\n\n{output_format}\n\n{examples}\n\n用户输入:\n__INPUT__"

    def _get_completion(self, prompt, model = "qianfan"):
        messages = [{"role": "user", "content": prompt}]
        prompt = PromptTemplates.from_template(self.prompt_template)
        
    # 用replace 将原来的prompt template中的 __INPUT__ 替换为函数返回的结果
    def add_detected_info_explain(self, prompt, enemy_status,  enemy_status_explain):
        add_prompt = prompt.replace("__DETECTED_STATUS__", enemy_status)
        add_prompt = add_prompt.replace("__DETECTED_STATUS_EXPLAIN__", enemy_status_explain)
        return add_prompt
    
    def add_our_info_explain(self, prompt ,  our_status, our_status_explain):
        add_prompt = prompt.replace("__OUR_STATUS__", our_status)
        add_prompt = add_prompt.replace("__OUR_STATUS_EXPLAIN__", our_status_explain)
        return add_prompt
    
    def add_our_status(self, prompt, our_status):  # 传入prompt_taishi["our_status"]
        add_prompt = prompt.replace("__OUR_STATUS__", our_status)
        return add_prompt
    
    def add_enemy_status(self, prompt, enemy_status): # 传入prompt_taishi["detected_status"]
        add_prompt = prompt.replace("__DETECTED_STATUS__", enemy_status)
        return add_prompt
    
    # background info 里面 
    def add_background_info(self, prompt, background_info):
        return prompt+background_info

    def get_example_input_output(self):
        eg = """
             下面是一个输入输出的例子，


        """


    def run_prompt(self):
        pass

    def set_num(self, num):
        self.num = num      #用于设定当前是推演到第几帧
    def set_deploy_points(self, our_point, enemy_point):
        self.our_deploy_point = our_point
        self.enemy_deploy_point = enemy_point

text_demo = "好的，按照你的格式给出作战指令：1. [move, ArmoredTruck_ZTL100_0, x=2.71, y=39.76], 移动我方无人战车ArmoredTruck_ZTL100_0到(2.59,39.72)处。2. [move, ArmoredTruck_ZTL100_1, x=2.71, y=39.76], 移动我方无人战车ArmoredTruck_ZTL100_1到(2.59,39.72)处。3. [move, Howitzer_C100_0, x=2.71, y=39.76], 移动我方自行迫榴炮Howitzer_C100_0到(2.59,39.72)处。4. [move, Infantry0, x=2.71, y=39.76], 移动我方步兵Infantry0到(2.59,39.72)处。5. [move, Infantry1, x=2.71, y=39.76], 移动我方步兵Infantry1到(2.59,39.72)处。6. [move, MainBattleTank_ZTZ100_0, x=2.71, y=39.76], 移动我方坦克MainBattleTank_ZTZ100_0到(2.59,39.72)处。7. [move, MainBattleTank_ZTZ100_1, x=2.71, y=39.76], 移动我方坦克MainBattleTank_ZTZ100_1到(2.59,39.72)处。8. [move, MainBattleTank_ZTZ100_2, x=2.71, y=39.76], 移动我方坦克MainBattleTank_ZTZ100_2到(2.59,39.72)处。9. [move, MainBattleTank_ZTZ100_3, x=2.71, y=39.76], 移动我方坦克MainBattleTank_ZTZ100_3到(2.59,39.72)处。10. [move, ShipboardCombat_plane0, x=2.71, y=39.76], 移动我方无人机ShipboardCombat_plane0到(2.59,39.72)处。...接下来的指令按照上述格式，给出每一步行动的指令..."

if __name__ == "__main__":
    # 测试一下
    shishi = text_transfer()
    commands = shishi.text_to_commands(text_demo)
    shishi.get_num_commands()
    pass 