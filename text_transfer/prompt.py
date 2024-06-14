from dotenv import load_dotenv
load_dotenv()    #加载环境变量
from langchain.prompts import PromptTemplates
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
# from langchain_community.llms import HuggingFaceHub
# 以qianfan为例 写functioncall
import qianfan
import re
#  使用方法 先调用  generate_prompt 生成 system prompt  之后LLM和后端平台展开多轮对话 调用generate_dialog 来将输入的态势简单封装一下
#  之后就可以发给LLM了

class PromptJSQL:
    def __init__(self):  
        #  以下这些只发送给LLM 一次
        self.role_template = """
        你是一个兵棋推演游戏的玩家，设想一个陆战作战场景，我方为红方，拥有坦克、步兵战车、自行迫榴炮和无人机等装备。这次陆战推演场景一共有{self.total_num}步，
        在每一步，我将告诉你敌我态势和地图相关信息，并由你来尝试生成作战指令。
        """ 
        self.cot_template = """
            作为一个兵棋推演的红方玩家，我们的目标是在夺取蓝方防守的夺控点，并利用我方装备尽可能攻击蓝方算子。我们知道夺控点的坐标。
            1.你需要清楚我方装备的当前位置，以及当前的推演帧
            2.你可以得到敌方装备的位置信息以及我方装备的位置信息，以及地图信息。
            3.基于这些信息，你需要去判断我方装备需要执行哪些动作，这些动作包括集结、移动和开火。
            再次强调一下，我们的目标是夺取夺控点，也就是指挥我方装备机动到夺控点所在的坐标。 
        """
        # 加入态势的垂直知识模板
        self.prompt_taishi_explain = {
            "detected_status": """
                 detected_status 表示探测到的敌方装备的信息
                 提供当前的敌方装备的类型和位置信息如下: __DETECTED_STATUS__ \n\n , 对上文叙述的解释如下: __DETECTED_STATUS_EXPLAIN__
                 需要你分析判断。
            """,
            "our_status": """
                 our_status 表示我方装备的信息
                 提供当前的我方装备的类型和位置信息: __OUR_STATUS__ \n\n ,对上文叙述的解释如下: __OUR_STATUS_EXPLAIN__ \n\n, 
                 需要你分析判断。
            """
        }
        self.prompt_taishi = {
            "detected_status": """
                 detected_status 表示探测到的敌方装备的信息
                 提供当前的敌方装备的类型和位置信息如下: __DETECTED_STATUS__ \n\n 
            """,
            "our_status": """
                 our_status 表示我方装备的信息
                 提供当前的我方装备的类型和位置信息: __OUR_STATUS__ \n\n 
            """
        }
        # 提供一些地图的背景知识E
        self.prompt_map_background = """
        \n\n
            地图的边界坐标为（2.60E, 39.85N）、(2.80E, 39.85N)、 (2.60E, 39.65N)、 (2.80E,39.65N) 我方（红方）的初始部署坐标为{self.our_deploy_point},敌方（蓝方）的初始部署坐标为{self.enemy_deploy_point}
            简单描述一下地图，地图西北方向为海洋，其余部分为陆地。陆地中间部分为山区，装备单位经过山区会由于坡度地形因素，导致行进速度减慢，
            夺控点周围是一片平原。
        \n\n
        """
        
        # 提供一些基础知识的背景 例如 装备的武力值 
        self.prompt_background = """
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

        self.prompt_detect_status_explain = """
        \n\n
           在前面的叙述中，每个obj_id表示探测到的敌方单位的ID，type 表示敌方装备类型，括号中内容分别对应lat、lon，lat、lon分别表示敌方装备当前所在的经度纬度和高度。你可以根据敌方装备类型和位置信息去判断敌方的行动计划并选择自身行动，估计下一次该敌方装备出现的位置。
           在自身动作选择上，你可以根据敌方装备类型和附近我方装备的情况去分析。例如，你可以通过当前敌方装备和我方装备的位置信息（lat、lon），计算出敌方算子到我方算子的距离，如果在我方武器射程内，则可以向敌方算子开火射击。
           再如，你可以通过敌方装备的类型和位置分布，推断出敌方装备的火力值和防御值，与当前我方装备进行比较，判断是否向前发动进攻还是向后撤退或者是进行迂回配合等作战行动。
        \n\n
         """
        self.prompt_our_status_explain = """
        \n\n
          在前面的叙述中，每个obj_id表示探测到的我方单位的ID，type 表示我方装备类型，括号中内容分别对应lat、lon，lat、lon分别表示敌方装备当前所在的经度纬度和高度。你可以根据敌方装备类型和位置信息去判断敌方的行动计划并选择自身行动，估计下一次该敌方装备出现的位置。
          在自身动作选择上，你可以根据敌方装备类型和附近我方装备的情况去分析。例如，你可以通过当前敌方装备和我方装备的位置信息（lat、lon），计算出敌方算子到我方算子的距离，如果在我方武器射程内，则可以向敌方算子开火射击。
          再如，你可以通过敌方装备的类型和位置分布，推断出敌方装备的火力值和防御值，与当前我方装备进行比较，判断是否向前发动进攻还是向后撤退或者是进行迂回等作战行动。
        \n\n
        """
        self.prompt_action_explain = """
        \n\n
            - 机动指令(move): [move, obj_id, act] ， 表示我方装备obj_id, 开始机动，方向：<前进>/<后退>/<向左迂回>/<向右迂回>
            - 开火指令(fire): [fire, obj_id] ，表示我方装备obj_id 用武器开火，打击敌方最近的装备。
            - 停止指令(stop): [stop, obj_id] ，表示我方装备obj_id 停止机动。
            - 集结指令(gather): [gather, obj_id, obj_id2] 表示我方装备obj_id1, obj_id2 向同一位置进发。
        \n\n
        """
        self.output_format = """
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
        self.thinking_examples = """
            下面是一个推演决策过程的例子，你需要学习这个例子中的从态势中获取关键信息来进行对我方装备的行动做出决策的过程。之后的推演中会给你发送当前态势，需要你自己推理出合理的决策。
            首先，读取
        
        """
        # 这部分是给输入的例子
        self.input_example1 = """
        \n\n 
        1. **当前是{self.num}帧
        2. **当前红方（我方）装备的位置信息是
        """ + self.add_our_status(self.prompt_taishi["our_status"], """
                        我方obj_id为ArmoredTruck_ZTL100_0的无人战车位置在(2.59,39.72)处 
                        我方obj_id为ArmoredTruck_ZTL100_1的无人战车位置在(2.59,39.72)处 
                        我方obj_id为Howitzer_C100_0的自行迫榴炮位置在(2.59,39.72)处 
                        我方obj_id为Infantry0的步兵位置在(2.59,39.72)处 
                        我方obj_id为Infantry1的步兵位置在(2.59,39.72)处 
                        我方obj_id为MainBattleTank_ZTZ100_0的坦克位置在(2.59,39.72)处 
                        我方obj_id为MainBattleTank_ZTZ100_1的坦克位置在(2.59,39.72)处 
                        我方obj_id为MainBattleTank_ZTZ100_2的坦克位置在(2.59,39.72)处 
                        我方obj_id为MainBattleTank_ZTZ100_3的坦克位置在(2.59,39.72)处 
                        我方obj_id为ShipboardCombat_plane0的无人机位置在(2.59,39.72)处 
                        我方obj_id为WheeledCmobatTruck_ZB100_0的步战车位置在(2.59,39.72)处 
                        我方obj_id为WheeledCmobatTruck_ZB100_1的步战车位置在(2.59,39.72)处 
                        我方obj_id为missile_truck0的导弹发射车位置在(2.6228,41.6363)处 
                        我方obj_id为missile_truck1的导弹发射车位置在(2.6238,41.6373)处 
                        我方obj_id为missile_truck2的导弹发射车位置在(2.6238,41.6373)处
        """) + """
        \n
        3. **当前蓝方（敌方）装备和位置信息是
        """ + self.add_enemy_status(self.prompt_taishi["detected_status"], """
            敌方obj_id为MainBattleTank_ZTZ200_3的坦克位置在(2.68984,39.7)处 
            敌方obj_id为Infantry3的步兵位置在(2.68618,39.7006)处 
            敌方obj_id为Infantry4的步兵位置在(2.68618,39.7006)处 
            敌方obj_id为MainBattleTank_ZTZ200_1的坦克位置在(2.68984,39.7)处 
            敌方obj_id为MainBattleTank_ZTZ200_0的坦克位置在(2.68984,39.7)处 
            敌方obj_id为ShipboardCombat_plane1的无人机位置在(2.68995,39.7)处 
            敌方obj_id为Infantry2的步兵位置在(2.68618,39.7006)处 
            敌方obj_id为WheeledCmobatTruck_ZB200_3的步战车位置在(2.68818,39.7026)处 
            敌方obj_id为MainBattleTank_ZTZ200_2的坦克位置在(2.68984,39.7)处 
            敌方obj_id为Infantry5的步兵位置在(2.68618,39.7006)处 
        """)
        # 这部分是给输出指令结果的例子
        self.output_example1 = """
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
        self.strategy_examples_gathering = """
                
        
        """
        
        self.strategy_examples_move = """

        
        """

        self.strategy_examples_openfire = """


        """

        self.chatcount = 0   # 用来控制对话轮数 
        # 这个prompt template 需要修改 
        self.total_num = 3000
        self.num = 0 
        # 敌我双方部署点信息
        self.our_deploy_point = None
        self.enemy_deploy_point = None
        #self.prompt_template = #f"{instruction}\n\n{output_format}\n\n{examples}\n\n用户输入:\n__INPUT__"

    # def _get_completion(self, prompt, model = "qianfan"):
    #     messages = [{"role": "user", "content": prompt}]
    #     prompt = PromptTemplates.from_template(self.prompt_template)
        
    # 用replace 将原来的prompt template中的 __INPUT__ 替换为函数返回的结果
    def add_detected_info_explain(self, prompt, enemy_status,  enemy_status_explain):
        add_prompt = prompt.replace("__DETECTED_STATUS__", enemy_status)
        add_prompt = add_prompt.replace("__DETECTED_STATUS_EXPLAIN__", enemy_status_explain)
        return add_prompt
    
    def add_our_info_explain(self, prompt ,  our_status, our_status_explain):
        add_prompt = prompt.replace("__OUR_STATUS__", our_status)
        add_prompt = add_prompt.replace("__OUR_STATUS_EXPLAIN__", our_status_explain)
        return add_prompt
    
    def add_our_status(self, prompt, our_status):    # 传入prompt_taishi["our_status"]
        add_prompt = prompt.replace("__OUR_STATUS__", our_status)
        return add_prompt
    
    def add_enemy_status(self, prompt, enemy_status): # 传入prompt_taishi["detected_status"]
        add_prompt = prompt.replace("__DETECTED_STATUS__", enemy_status)
        return add_prompt
    
    # background info 里面 
    def add_background_info(self, prompt, background_info):
        return prompt+background_info

    def get_example_input_output(self):
        return  """
             下面是一个输入输出的例子，输入是当前敌我双方的态势信息：
             ----example input-----
             {self.input_example1}
             经过推理后，输出我方各装备下一步的指令动作：
             ----example output----
             {self.output_example1}
        """
    def generate_prompt(self):
        prompt_templates = dict()
        prompt_templates["sys_prompt"] =  self.role_template + self.cot_template 
        prompt_templates["background_prompt"] = self.prompt_background + self.prompt_map_background
        prompt_templates["parsestatus_prompt"] = self.add_detected_info_explain(self.prompt_taishi_explain["detected_status"], \
                  self.input_example1,  self.prompt_detect_status_explain) + \
                  self.add_our_info_explain(self.prompt_taishi_explain["our_status"] + \
                  self.input_example1,  self.prompt_our_status_explain)
        prompt_templates["test_example"] = self.get_example_input_output(self.prompt_taishi_explain["our_status"], 
                self.output_example1,   self.prompt_our_status_explain)
        prompt_templates["output_prompt"] = self.output_format + self.prompt_action_explain

        return prompt_templates
    def generate_dialog(self, our_status, detect_status):
        dialog = self.add_our_status(our_status) + "\n\n" + self.add_enemy_status(detect_status)
        return dialog
    
    def run_prompt(self):
        pass
    def set_num(self, num):
        self.num = num      #用于设定当前是推演到第几帧
    def set_deploy_points(self, our_point, enemy_point):
        self.our_deploy_point = our_point
        self.enemy_deploy_point = enemy_point
        