# prompt模板使用Jinja2语法，简单点就是用双大括号代替f-string的单大括号
# 本配置文件支持热加载，修改prompt模板后无需重启服务。

# LLM对话支持的变量：
#   - input: 用户输入内容

# Agent对话支持的变量：

#   - tools: 可用的工具列表
#   - tool_names: 可用的工具名称列表
#   - history: 用户和Agent的对话历史
#   - input: 用户输入内容
#   - agent_scratchpad: Agent的思维记录
from text_transfer.prompt import PromptJSQL
promptJSQL = PromptJSQL()
embrace_background_dict =  promptJSQL.generate_prompt()
embrace_lang =  embrace_background_dict["sys_prompt"] + embrace_background_dict["background_prompt"] +\
      embrace_background_dict["parsestatus_prompt"] + embrace_background_dict["test_example"] + embrace_background_dict["output_prompt"]

PROMPT_TEMPLATES = {
    "llm_chat": {
        "default":
            '{{ input }}',

        "with_history":
            'Answer my questions considering the coversation history.'
            'If you do not know the answer, just say do not know. \n\n'
            'Current conversation:\n'
            '{history}\n',
            
        # "embrace":
        #     '请作为兵棋推演游戏的玩家，设想一个陆战作战场景。'
        #     '我方为红方，拥有坦克、步兵战车、自行迫榴炮、无人突击车和无人机、导弹发射车等装备，步兵下车后作战，'
        #     '我方需要攻取位于经纬度坐标(2.7100,39.7600)的夺控点，要将陆战装备移动到夺控点处并消灭夺控点附近敌人，地图范围为经度2.6000到2.8000，纬度范围为39.6500到39.8500，导弹发射车不能机动。地图西北方向为海洋，其余部分为陆地。陆地中间部分为山区，装备单位经过山区会由于坡度地形因素，导致行进速度减慢，夺控点周围是一片平原。'
        #     '每隔一定步数，我将告诉你敌我态势和其他信息，并由你来尝试生成作战指令。\n'
        #     '在生成指令时，可以考虑历史态势和指令，下面是我们的对话历史：\n'
        #     '{history}'
        #     '请按照以下格式给出作战指令。进攻指令：[move, obj_id , x=int, y=int], 如坦克mbt_1进攻坐标为(2.7100, 39.7600)，则指令为[move, obj_id=mbt_1, x=2.7100, y=39.7600] \n停止指令：[stop, obj_id], 如坦克mbt_1停止当前行动，则指令为[stop, obj_id=mbt_1] \n步兵下车指令: [off_board, obj_id],如步战车ifv_1内步兵立刻下车,则指令为[off_board, obj_id=ifv_1]'
    
        #
        "embrace": embrace_lang + '在生成指令时，可以考虑历史态势和指令，下面是我们的对话历史：\n {history}'
    
    
    }
}
