# 这个用来实现“JSON态势转化成文本态势”，以及约定一些命令的信息

# 需要约定一下命令格式了。


class text_transfer(object):
    def __init__(self) -> None:
        self.command_type_list = ["move", "stop"]
        pass

    def status_to_text(self, status):
        print("status_to_text unfinished yet,return a demo")
        status_str = "我方坦克位置在(27.5,27.5)处"
        return status_str
    
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
    
    def get_initial_prompt(self, text:str):
        print("get_initial_prompt unfinished yet,return a demo")
        initial_prompt = "这是一个作战场景，我方坦克mbt_1在(27.5,27.5), 敌方坦克在(100, 100)"
        # 还需要一些描述地图的prompt
        return initial_prompt
    
    def get_order_guize(self, text):
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
    
