# 这个用来实现“JSON态势转化成文本态势”，以及约定一些命令的信息

# 需要约定一下命令格式了。

import json
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
        initial_prompt = "请作为兵棋推演游戏的玩家，设想一个陆战作战场景，我方为红方，拥有坦克、步兵战车、自行迫榴炮和无人机等装备，步兵下车后作战，我方需要攻取位于经纬度坐标(2.68,39.74)的夺控点。在每一步，我将告诉你敌我态势和其他信息，并由你来尝试生成作战指令。"
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

#@ szh 0605 先写几个prompt 试一下 
# 目前想的几个点 
# 1 可以做成多轮对话的 看看效果  也就是加一个memory去存  
# 2 对话要带帧数
# 3 后面可以设置配置文件，并读取配置文件来 
# 4 最好是得引导LLM 一步一步来 
from dotenv import load_dotenv
load_dotenv()    #加载环境变量
from langchain.prompts import PromptTemplates
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
# from langchain_community.llms import HuggingFaceHub
# model = HuggingFaceHub(repo_id = "")

# 以qianfan为例 写functioncall
import qianfan
import re


class PromptJSQL:
    def __init__(self):


        #  以下这些只发送给LLM 一次
        role_template = """
        你是一个兵棋推演游戏的玩家，设想一个陆战作战场景，我方为红方，拥有坦克、步兵战车、自行迫榴炮和无人机等装备，在每一步，我将告诉你敌我态势和地图相关信息，并由你来尝试生成作战指令。
        """ 
        cot_template = """
            作为一个兵棋推演的红方玩家，我们的目标是在夺取蓝方防守的夺控点，并利用我方装备尽可能攻击蓝方算子。我们知道夺控点的坐标。首先，你需要清楚自己当前的位置，以及当前位置
            然后你可以得到敌方装备的位置信息以及我方装备的位置信息，以及地图信息。基于这些信息，你需要去判断我方装备需要执行哪些动作，这些动作包括集结、移动和开火。再次强调一下，我们的目标是夺取夺控点, 
            你需要综合考虑。 
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
        # 提供一些基础知识的背景 例如 装备的武力值 
        prompt_background = """
            这里给出兵棋推演中的一些基本背景信息，包括装备编成、装备火力值、装备防御值、装备机动速度、装备射程等。你可以认为红蓝双方相同类型的装备具有相同的火力值、射程等参数。例如，红方坦克的射程为2500m，那么可以认为蓝方坦克的射程也为2500m。
            火力值反映了装备对敌方装备的打击毁伤能力，火力值越大，毁伤能力越强，数值表示相对大小。 装备防御值反映了装备对敌方攻击的防御能力，防御值越大，防御能力越强。
            先说明装备编成，本次推演中，我方作为红方，初始时拥有2个步兵班、4辆坦克、2辆无人突击车、一架无人机。 敌方作为蓝方，初始时具有4辆装甲车、4个步兵班、4辆装甲车，一架无人机。
            下面给出各装备的火力值，坦克有穿甲弹和高爆弹，火力值为150。 步战车配备有机枪，火力值为50。 步兵班配备火箭炮，火力值为100。无人机作为侦察装备，配备4枚空对地，火力值为80。无人突击车配备两枚RPG，火力值为80
            下面给出各类型装备的机动速度，坦克机动速度为58km/h、装甲车机动速度为72km/h，步兵班机动速度为10km/h，无人突击车机动速度为108km/h,无人机速度为198km/h。
            下面给出各类型装备的防御值，数值为相对大小。坦克防御值为200，步兵班为140， 无人突击车为80， 装甲车为80，无人机为80。请注意，无人机为空中装备。
            下面给出各类型装备的射程，坦克射程为2500m， 装甲车为1000m，步兵班为1000m，无人突击车为2500m， 无人机为4000m
            在本次推演中，你不需要考虑装备的配弹量和剩余弹量。
        """

        prompt_detect_status_explain = """
           在前面的JSON中，每个key表示探测到的敌方单位，type 表示敌方装备类型， lat、lon、alt,分别表示敌方装备当前所在的经度纬度和高度。你可以根据敌方装备类型和位置信息去判断敌方的行动计划并选择自身行动，估计下一次该敌方装备出现的位置。
           在自身动作选择上，你可以根据敌方装备类型和附近我方装备的情况去分析。例如，你可以通过当前敌方装备和我方装备的位置信息（lat、lon、alt），计算出敌方算子到我方算子的距离，如果在我方武器射程内，则可以向敌方算子开火射击。
           再如，你可以通过敌方装备的类型和位置分布，推断出敌方装备的火力值和防御值，与当前我方装备进行比较，判断是否向前发动进攻还是向后撤退或者是进行迂回配合等作战行动。
        """
        prompt_our_status_explain = """
          在前面的JSON中，每个key表示探测到的我方单位，type 表示敌方装备类型， lat、lon、alt,分别表示敌方装备当前所在的经度纬度和高度。你可以根据敌方装备类型和位置信息去判断敌方的行动计划并选择自身行动，估计下一次该敌方装备出现的位置。
           在自身动作选择上，你可以根据敌方装备类型和附近我方装备的情况去分析。例如，你可以通过当前敌方装备和我方装备的位置信息（lat、lon、alt），计算出敌方算子到我方算子的距离，如果在我方武器射程内，则可以向敌方算子开火射击。
           再如，你可以通过敌方装备的类型和位置分布，推断出敌方装备的火力值和防御值，与当前我方装备进行比较，判断是否向前发动进攻还是向后撤退或者是进行迂回等作战行动。
        """

        output_format = """
        以JSON格式输出。
        1.  


        """
        
        # 这部分是给出一个思考过程的例子
        thinking_examples = """
            下面是一个推演决策过程的例子，你需要学习这个例子中的从态势中获取关键信息来进行对我方装备的行动做出决策的过程。之后，我们我给你发送当前态势，需要你自己推理出合理的决策。
            首先，读取
        
        """

        # 这部分是给输出指令结果的例子
        output_examples = """
        

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
    
    # background info 里面 
    def background_info(self, background_info):
        pass


    # 
    def run_prompt(self):
        pass