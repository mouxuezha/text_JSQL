# 这个是主函数，到时候就运行这个就完事了。
import agent_guize.agent as agent
import text_transfer.text_transfer as text_transfer
import model_communication.model_communication as model_communication

class command_processor:
    
    def __init__(self):
        pass

    def run_one_step_with_LLM(self):
        # 从agent把态势拿出来
        # 把态势转成大模型能看懂的文本形式
        # 检测是否人混的干预，有的话也弄进去
        # 把文本发给大模型，获取返回来的文本
        # 把文本里面的命令提取出来
        # 把提取出来的命令发给agent，让它里面设定抽象状态啥的。
        pass

    def human_intervene_check(self):
        # 输入输出怎么做还两说呢，整个窗口？然后用信号槽机制实现人输入的这个异步，可行。
        

        pass