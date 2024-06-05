# 这个用来实现“JSON态势转化成文本态势”，以及约定一些命令的信息

# 需要约定一下命令格式了。


class text_transfer(object):
    def __init__(self) -> None:
        self.command_type_list = ["move", "stop"]
        self.type_transfer = type_transfer() 
        pass

    def status_to_text(self, status):
        print("status_to_text unfinished yet,return a demo")
        status_str = ""
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
                status_str +="我方obj_id为"+str(obj_id)+"的"
                status_str += f"{unit_type_zhongwen}位置在({lon},{lat})处 \n"
        return status_str
    
    def detected_to_text(self, detected_state):
        # 这里面的探测到的数据结构还不太一样，所以需要另外开一个函数来实现
        detected_str = ""
        for obj_id in list(detected_state.keys()):
            detected_status = detected_state[obj_id]
            lon = detected_status["targetLon"]
            lat = detected_status["targetLat"]
            alt = detected_status["targetAlt"]
            detected_type_zhongwen = self.type_transfer.unit_type_transfer(detected_status["unitType"])
            if detected_type_zhongwen == "其他":
                continue
            else:
                detected_str +="敌方obj_id为"+str(obj_id)+"的"
                detected_str += f"{detected_type_zhongwen}位置在({lon},{lat})处 \n"
        print(detected_str)
        return detected_str
        pass 


    def text_to_commands(self, text:str):
        print("text_to_commands unfinished yet,return a demo")
        
        commands = []
        for command_type in self.command_type_list:
            if command_type == "move":
                index_list = self.find_all_str(text, command_type)
                for index in index_list:
                    # 还要把坐标抠出来
                    sub_str = text.find(text, index + 1)
                    x = float(self.cut_from_str(sub_str, "x=", ","))
                    y = float(self.cut_from_str(sub_str, "y=", ","))
                    obj_id = self.cut_from_str(sub_str, "obj_id=", ",")
                    command_single = {"type": command_type, "obj_id": obj_id, "x": x, "y": y}
                    commands.append(command_single)
            elif command_type == "stop":
                index_list = self.find_all_str(text, command_type)
                for index in index_list:
                    sub_str = text.find(text, index + 1)
                    obj_id = self.cut_from_str(sub_str, "obj_id=", ",")
                    command_single = {"type": command_type, "obj_id": obj_id}
                    commands.append(command_single)
        return commands
    
    def get_initial_prompt(self):
        print("get_initial_prompt unfinished yet,return a demo")
        initial_prompt = "请作为兵棋推演游戏的玩家，设想一个陆战作战场景，我方为红方，拥有坦克、步兵战车、自行迫榴炮和无人机等装备，步兵下车后作战，我方需要攻取位于经纬度坐标(2.68,39.74)的夺控点的，地图范围为。在每一步，我将告诉你敌我态势和其他信息，并由你来尝试生成作战指令。"
        # 还需要一些描述地图的prompt
        return initial_prompt
    
    def get_order_guize(self):
        # 这里面是给大模型设定的规则的格式。
        order_guize = "请按照以下格式给出作战指令。进攻指令：[move, obj_id , x=int, y=int], 如坦克mbt_1进攻坐标为(100, 100)，则指令为[move, obj_id=mbt_1, x=100, y=100] \n 停止指令：[stop, obj_id], 如坦克mbt_1停止当前行动，则指令为[stop, obj_id=mbt_1]。"
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
        index_hou = text.find(str_hou)
        number_str = text[index_qian+1:index_hou]
        # number_float = float(number_str)
        return number_str
    
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