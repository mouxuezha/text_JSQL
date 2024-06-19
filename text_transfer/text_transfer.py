# 这个用来实现“JSON态势转化成文本态势”，以及约定一些命令的信息

# 需要约定一下命令格式了。


class text_transfer(object):
    def __init__(self) -> None:
        self.command_type_list = ["move", "stop", "off_board"]
        self.type_transfer = type_transfer() 
        self.num_commands = [0,0] # 第一个是转化成功的commands，第二个是转化失败的commands 
        pass

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
                status_str +="我方obj_id为"+str(obj_id)+"的"
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
                detected_str +="敌方obj_id为"+str(obj_id)+"的"
                detected_str += f"{detected_type_zhongwen}位置在({lon},{lat})处 \n"
        print(detected_str)
        return detected_str
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

text_demo = "好的，按照你的格式给出作战指令：1. [move, ArmoredTruck_ZTL100_0, x=2.71, y=39.76], 移动我方无人战车ArmoredTruck_ZTL100_0到(2.59,39.72)处。2. [move, ArmoredTruck_ZTL100_1, x=2.71, y=39.76], 移动我方无人战车ArmoredTruck_ZTL100_1到(2.59,39.72)处。3. [move, Howitzer_C100_0, x=2.71, y=39.76], 移动我方自行迫榴炮Howitzer_C100_0到(2.59,39.72)处。4. [move, Infantry0, x=2.71, y=39.76], 移动我方步兵Infantry0到(2.59,39.72)处。5. [move, Infantry1, x=2.71, y=39.76], 移动我方步兵Infantry1到(2.59,39.72)处。6. [move, MainBattleTank_ZTZ100_0, x=2.71, y=39.76], 移动我方坦克MainBattleTank_ZTZ100_0到(2.59,39.72)处。7. [move, MainBattleTank_ZTZ100_1, x=2.71, y=39.76], 移动我方坦克MainBattleTank_ZTZ100_1到(2.59,39.72)处。8. [move, MainBattleTank_ZTZ100_2, x=2.71, y=39.76], 移动我方坦克MainBattleTank_ZTZ100_2到(2.59,39.72)处。9. [move, MainBattleTank_ZTZ100_3, x=2.71, y=39.76], 移动我方坦克MainBattleTank_ZTZ100_3到(2.59,39.72)处。10. [move, ShipboardCombat_plane0, x=2.71, y=39.76], 移动我方无人机ShipboardCombat_plane0到(2.59,39.72)处。...接下来的指令按照上述格式，给出每一步行动的指令..." + "6. [move, MainBattleTank_ZTZ100_0, x=2sadas76], 移动我方坦克MainBattleTank_ZTZ100_0到(2.59,39.72)处。7. [move, MainBattleTank_ZTZ100_1, x=asdsa.76], 移动我方坦克MainBattleTank_ZTZ100_1到(2.59,39.72)处。8. [move, MainBattleTank_ZTZ1asdas1, y=39.76], 移动我方坦克MainBattleTank_ZTZ100_2到(2.59,39.72)处。9. [move, MainBattleTank_ZTZ100_3, x=2.asdsa.76], 移动我方坦克MainBattleTank_ZTZ100_3到(2.59,39.72)处。10. [move, ShipboardCombat_plane0, x=2asdsa9.76], 移动我方无人机ShipboardCombat_plane0到(2.59,39.72)处。...接下来的指令按照上述格式，给出每一步行动的指令..."

if __name__ == "__main__":
    # 测试一下
    shishi = text_transfer()
    commands = shishi.text_to_commands(text_demo)
    shishi.get_num_commands()
    pass 