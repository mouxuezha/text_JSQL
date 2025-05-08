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

        self.__init_type()
    
    def __init_type(self):
        # 这个就是把那些ID的类型弄过来整成一个列表以备后用。
        # 红方坦克：MainBattleTank_ZTZ100，蓝方坦克：MainBattleTank_ZTZ200，红方步兵战车：WheeledCmobatTruck_ZB100，蓝方步兵战车：WheeledCmobatTruck_ZB200，步兵班：Infantry，自行迫榴炮：Howitzer_C100，无人突击车：ArmoredTruck_ZTL100，无人机：ShipboardCombat_plane，导弹发射车：missile_truck。
        self.type_list = ["MainBattleTank_ZTZ100","MainBattleTank_ZTZ200","WheeledCmobatTruck_ZB100","WheeledCmobatTruck_ZB200","Infantry","Howitzer_C100","ArmoredTruck_ZTL100","ShipboardCombat_plane","missile_truck","JammingTruck","RedCruiseMissile","BlueCruiseMissile"]
        self.type_list_CN = ["坦克","坦克","步兵战车","步兵战车","步兵班","自行迫榴炮","无人突击车","无人机","导弹发射车","电子干扰车","巡飞弹","巡飞弹"]
        self.command_type_list = ["move","stop","offboard"] # 
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
            
            # 当前装备是红方还是蓝方得读相应的字段来体现了。
            if unit_status["PlayerName"] == "redPlayer":
                side_name = "红方"
                pass
            elif unit_status["PlayerName"] == "bluePlayer":
                side_name = "蓝方"
                pass
            else:
                side_name = "其他"

            if unit_type_zhongwen == "其他":
                # 什么BMC3那些就别拿进来了
                continue
            else:
                status_str += side_name + "obj_id为"+str(obj_id)+"的"
                status_str += f"{unit_type_zhongwen}位置在({lon},{lat})处 \n"
        return status_str
    
    def status_to_text2(self,status_json):
        # 这个是来一个简化版的，只说有几个什么东西了。
        # 这个把读出来的JSON文件转换成一段叙述。
        unit_all = status_json
        unit_all_list = list(unit_all.keys())
        result_text_red = "红方："
        result_text_blue = "蓝方："
        for unit_type in self.type_list:
            count_red = 0 
            count_blue = 0 
            record_LLA_red = [] 
            record_LLA_blue = [] 
            record_ID_red = [] 
            record_ID_blue = []             
            for unit_id_single in unit_all_list:
                if unit_type in unit_id_single:
                    
                    lon = unit_all[unit_id_single]["VehicleState"]["lon"]
                    lat = unit_all[unit_id_single]["VehicleState"]["lat"]
                    
                    if unit_all[unit_id_single]["PlayerName"] == "redPlayer":
                        count_red += 1
                        record_LLA_red.append([lon,lat])
                        record_ID_red.append(unit_id_single)
                    else:
                        count_blue += 1
                        record_LLA_blue.append([lon,lat])
                        record_ID_blue.append(unit_id_single)
            # 1112增加的说法：得把坐标也想个办法弄进来

            #然后生成一段话
            if count_red != 0:
                result_text_red += self.type_list_CN[self.type_list.index(unit_type)] + "有" + str(count_red) + "个，obj_id为" + str(record_ID_red)
            if count_blue != 0:
                result_text_blue += self.type_list_CN[self.type_list.index(unit_type)] + "有" + str(count_blue) + "个，obj_id为" + str(record_ID_blue)
            result_text = result_text_red + result_text_blue
        return result_text        

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
                detected_str +="目标obj_id为"+str(obj_id)+"的"
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
        enemy_in_range_dict = self.find_nearest_enemy(our_tank_lat_avg, our_tank_lon_avg, detect_state, 2500)
        enemy_in_range_renhua =  self.turn_dict_to_renhua(enemy_in_range_dict)
        # messages = f"""
        #     当前探测到对方主力装备位于我方装备的{enemy_direct}方向，我方平均距离为{group_dis} , 敌方在我方射程范围内的装备有 {enemy_in_range_renhua}, 
        # """

        # xxh20241122:如果没有探测到就别要这段了。
        if len(detect_state)>0:
            # 有探测再来这个，没有探测就别来了。
            messages = f"探测到敌方在{enemy_direct}方向，平均距离" + str(round(group_dis,1)) + "米"
            if len(enemy_in_range_renhua)>0:
                messages = messages + ", 射程内敌人有" +str(enemy_in_range_renhua)+","
            if self.check_enemy_closer_to_target(enemy_tank_lon_avg, enemy_tank_lat_avg):
                left_time = self.distance(enemy_tank_lon_avg, enemy_tank_lat_avg, 0, self.tar_lon, self.tar_lat, 0)/20
                left_time = int(left_time)
                messages += f" 敌预计 {left_time}后到达夺控点" 
        else:
            messages = "注意，尚未探测到敌人。"
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
                        try:
                            # 再来一层容错，不然遇到能力不够的就傻逼了。
                            x = float(self.cut_from_str(sub_str, "x=", ","))
                        except:
                            x = 100.138
                            print("坐标识别失败，来个容错")
                        try:
                            y = float(self.cut_from_str(sub_str, "y=", "]"))
                        except:
                            y = 13.644
                            print("坐标识别失败，来个容错")
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
        initial_prompt = '请作为兵棋推演游戏的玩家，设想一个陆战攻防场景。'
        '我方为红方，拥有坦克、步兵战车、步兵、自行迫榴炮、无人突击车、巡飞弹、无人机、导弹发射车、电子干扰车等装备，步兵下车后作战，'
        '我方需要攻取位于经纬度坐标(100.1247, 13.6615)的夺控点，将陆战装备移动到夺控点处并消灭夺控点附近敌人可占领夺控点，地图范围为经度100.0923到100.18707，纬度范围为13.6024到13.6724，导弹发射车不能机动。'
        '每隔一定步数，我将告诉你敌我态势和其他信息，并由你来尝试生成作战指令。\n'
        # 还需要一些描述地图的prompt
        initial_prompt = initial_prompt + "地图大部分为陆地，具有河流、桥梁和路网，在经纬度坐标(100.137,13.644),(100.116,13.643),(100.164,13.658)有可供步兵占领和建立防线的建筑物。"
        return initial_prompt
    
    def get_order_guize(self):
        # 这里面是给大模型设定的规则的格式。
        order_guize = '请按照以下格式给出作战指令。进攻指令：[move, obj_id , x=int, y=int], 如坦克mbt_1进攻坐标(100.1247, 13.6615)，则指令为[move, obj_id=mbt_1, x=100.1247, y=13.6615] \n停止指令：[stop, obj_id], 如坦克mbt_1停止当前行动，则指令为[stop, obj_id=mbt_1] \n步兵下车指令: [off_board, obj_id],如步战车ifv_1内步兵立刻下车,则指令为[off_board, obj_id=ifv_1]'
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
        str_buffer = str_buffer + "\n识别成功率：" + str(self.num_commands[0]/(self.num_commands[0]+self.num_commands[1]+0.0000001))
        
        print(str_buffer)
        return str_buffer

    def response_wrap(self, response_str:str):
        # 这个是包装一下
        wrapped_str = "{\"SchemesDataList\":[],\"msgCommid\":\""+response_str+"\"}"        
        wrapped_str = wrapped_str.replace("'", "\"")
        return wrapped_str
    
    def response_wrap2(self, response_str:str):
        # 这搞法不理想，通信部分随便改个啥都要改，远没有直接序列化反序列化丝滑。
        wrapped_str = "{\"SchemesDataList\":\""+response_str+"\",\"msgCommid\":[]}"        
        wrapped_str = wrapped_str.replace("'", "\"")        
    
    def response_wrap_dict(self, response_dict):
        communication_dict = {}
        communication_dict["SchemesDataList"] = []
        communication_dict["msgCommid"] = response_dict

        # 然后转成str给它冲了
        wrapped_str = str(communication_dict)
        wrapped_str = wrapped_str.replace("'", "\"")
        return wrapped_str
    
    def str_squeeze(self,str_input,len_max=300):
        # 这个就是如果字符串太多了就把中间部分略去，搞成显示出来不那么抽象的效果。
        
        len_qian = int(len_max*2/3) 
        len_hou = int(len_max*1/3)
        
        # 先前处理一下
        str_input = self.clean_the_str2(str_input)
        zishu = len(str_input)

        if zishu > len_max:
            # 那就启动压缩。
            
            str_qian = str_input[0:len_qian]
            str_hou = str_input[zishu-len_hou:-1]
            str_zhongjian = "……【过长显示已折叠】……"
            str_output = str_qian + str_zhongjian + str_hou
        else:
            str_output = str_input
        
        return str_output
    def del_note_from_str(self, input_str:str):
        str_qian = "//"
        str_hou = "\n"

        str_qianhou_list = [] 
        str_qianhou_list.append(["//","\n"])
        str_qianhou_list.append(["（","）"])
        str_qianhou_list.append(["(",")"])
        
        output_str = input_str
        for str_qianhou in str_qianhou_list:
            str_qian = str_qianhou[0]
            str_hou = str_qianhou[1]
        
            while(str_qian in output_str):
                index_qian = output_str.find(str_qian)
                sub_str = output_str[index_qian:]
                index_hou = sub_str.find(str_hou)
                sub_str2 = sub_str[0:index_hou]
                output_str = output_str.replace(sub_str2, "") # 也行吧，AI给出来的这个写法比我想的似乎还舒服一些。

        return output_str
    
    def clean_the_str(self, input_str:str):
        # 这个是清理字符串的，把一些没用的符号去掉.
        clean_list = ["**","//"]
        for clean_str in clean_list:
            while clean_str in input_str:
                input_str = input_str.replace(clean_str,"")

        # 然后特殊处理。
        while "\n\n" in input_str:  
            input_str = input_str.replace("\n\n","\n")

        # 然后继续特殊处理，把json切走。
        if "json" in input_str:
            # 那就是说里面有怪东西
            index_qian = input_str.find("json")
            sub_str = input_str[index_qian:]
            if "```" in sub_str:
                index_hou = sub_str.rfind("```")
            else:
                index_hou = sub_str.find("}")
            
            input_str = input_str.replace(sub_str[0:index_hou+1],"")

        return input_str
    
    def clean_the_str2(self,input_str:str):
        # 为了防止影响别的地方的json识别，把输入的字符串里面的会影响的东西都弄走。
        clean_list = ["json","```","``","`","{","}","\n","\\n"," ","    "]
        for clean_str in clean_list:
            while clean_str in input_str:
                input_str = input_str.replace(clean_str,"")
        
        # 然后保险起见把英文标点符号都弄成中文的。
        input_str = input_str.replace("\"","“")
        input_str = input_str.replace(":","：")
        input_str = input_str.replace(",","，")
        input_str = input_str.replace("(","（")
        input_str = input_str.replace(")","）")
        input_str = input_str.replace("[","（")
        input_str = input_str.replace("]","）")

        return input_str

    def get_json_str_debug(self, prompt:str):
        print("get_json_str_debug: 这个是用于调试的，正式版本中不应该出现")
        
        if "开始推演" in prompt:
            # 模拟接收前端操作：点击开始按钮。
            message_json = {"command":"开始推演"} # 这里面就是回头应该跟雪楠哥他们的对的消息格式了。
        elif "停止推演" in prompt:
            # 模拟接收前端操作：点击停止按钮
            message_json = {"command":"结束推演"}
        
        return message_json

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
            'CruiseMissile': '巡飞弹',
            'JammingTruck': '干扰车'
        }
    def unit_type_transfer(self, unit_type:str):
        for key in list(self.unit_type_dict.keys()):
            if key in unit_type:
                unit_type_zhongwen = self.unit_type_dict[key]
                break
            else:
                unit_type_zhongwen = "其他"
        return unit_type_zhongwen
    
    
# text_demo = "好的，按照你的格式给出作战指令：1. [move, ArmoredTruck_ZTL100_0, x=2.71, y=39.76], 移动我方无人战车ArmoredTruck_ZTL100_0到(2.59,39.72)处。2. [move, ArmoredTruck_ZTL100_1, x=2.71, y=39.76], 移动我方无人战车ArmoredTruck_ZTL100_1到(2.59,39.72)处。3. [move, Howitzer_C100_0, x=2.71, y=39.76], 移动我方自行迫榴炮Howitzer_C100_0到(2.59,39.72)处。4. [move, Infantry0, x=2.71, y=39.76], 移动我方步兵Infantry0到(2.59,39.72)处。5. [move, Infantry1, x=2.71, y=39.76], 移动我方步兵Infantry1到(2.59,39.72)处。6. [move, MainBattleTank_ZTZ100_0, x=2.71, y=39.76], 移动我方坦克MainBattleTank_ZTZ100_0到(2.59,39.72)处。7. [move, MainBattleTank_ZTZ100_1, x=2.71, y=39.76], 移动我方坦克MainBattleTank_ZTZ100_1到(2.59,39.72)处。8. [move, MainBattleTank_ZTZ100_2, x=2.71, y=39.76], 移动我方坦克MainBattleTank_ZTZ100_2到(2.59,39.72)处。9. [move, MainBattleTank_ZTZ100_3, x=2.71, y=39.76], 移动我方坦克MainBattleTank_ZTZ100_3到(2.59,39.72)处。10. [move, ShipboardCombat_plane0, x=2.71, y=39.76], 移动我方无人机ShipboardCombat_plane0到(2.59,39.72)处。...接下来的指令按照上述格式，给出每一步行动的指令..."

text_demo = '进攻指令：\n[move, obj_id=MainBattleTank_ZTZ100_0, x=100.138, y=13.6196],\n[move, obj_id=MainBattleTank_ZTZ100_1, x=100.138, y=13.6196],\n[move, obj_id=MainBattleTank_ZTZ100_2, x=100.138, y=13.6196],\n[move, obj_id=MainBattleTank_ZTZ100_3, x=100.138, y=13.6196],\n[move, obj_id=ArmoredTruck_ZTL100_0, x=100.138, y=13.6196],\n[move, obj_id=ArmoredTruck_ZTL100_1, x=100.138, y=13.6196],\n[move, obj_id=WheeledCmobatTruck_ZB100_0, x=100.138, y=13.6196],\n[move, obj_id=WheeledCmobatTruck_ZB100_1, x=100.138, y=13.6196],\n[move, obj_id=Howitzer_C100_0, x=100.138, y=13.6196],\n[move, obj_id=ShipboardCombat_plane0, x=100.137, y=13.644],\n[move, obj_id=RedCruiseMissile_0, x=100.116, y=13.643],\n[move, obj_id=RedCruiseMissile_1, x=100.164, y=13.658]'

text_demo_blue = '进攻指令：\n[move, obj_id=MainBattleTank_ZTZ200_0, x=100.138, y=13.6196],\n[move, obj_id=MainBattleTank_ZTZ200_1, x=100.138, y=13.6196],\n[move, obj_id=MainBattleTank_ZTZ200_2, x=100.138, y=13.6196],\n[move, obj_id=MainBattleTank_ZTZ200_3, x=100.138, y=13.6196],\n[move, obj_id=WheeledCmobatTruck_ZB200_0, x=100.138, y=13.6196],\n[move, obj_id=WheeledCmobatTruck_ZB200_1, x=100.138, y=13.6196],\n[move, obj_id=ShipboardCombat_plane1, x=100.137, y=13.644],\n[move, obj_id=BlueCruiseMissile_0, x=100.116, y=13.643],\n[move, obj_id=BlueCruiseMissile_1, x=100.164, y=13.658]'


if __name__ == "__main__":
    # 测试一下
    shishi = text_transfer()
    commands = shishi.text_to_commands(text_demo)
    shishi.get_num_commands()
    pass 