# 这个是一个用于实现大模型解说的接口。理想的情形是，只要往这里面不断地填.
# 要考虑可分割可维护的特性。因为大模型解说和大模型辅助决策未必是同时用的东西。
import os.path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from text_transfer.text_transfer import text_transfer, text_demo
from text_transfer.stage_prompt import StagePrompt
from model_communication.model_communication import model_communication, model_communication_debug
from model_communication.model_comm_langchain import ModelCommLangchain
from TTS.TTS_generator import *

import copy
import threading
import time

class TTS_interface():

    def __init__(self):
        self.status_list = [] 
        self.pcm_name_list = [] 
        self.max_list_num = 10 
        self.min_list_num = 2
        self.index_generate = 0 
        self.index_play = 0 

        self.LLM_model = "zhipu" # 这里可以改，默认是qianfan,还有智谱啥的
        self.model_communication = model_communication_debug(Comm_type ="jieshuo")
        # self.model_communication = ModelCommLangchain(model_name=self.LLM_model,Comm_type ="jieshuo")
        self.TTS_generator = TTS_generator()
        # 要用多个的话等后面再来改罢。        
        pass

    def input_new_status(self,status_str):
        # 到时候只要不断地往这里面塞入态势信息就行了，剩下的尽量闭环在这里面。

        # 态势存一个列表好了，每次都取用最新的，长度太长了就删掉前面的。这也不完全是个堆栈。算了自己弄一下好了。
        pass
    
    def add_status_list(self,status_str):
        # 操作self.status_list
        
        # 如果是重复的就不加进去了。
        if status_str != self.status_list[-1]:
            self.status_list.append(status_str)
            geshu = len(self.status_list)
            if geshu>self.max_list_num:
                # 超过了就把之前存的删了。
                del self.status_list[0]

    def pop_status_list(self):
        # 操作self.status_list. 其实这里不需要多个多个取出来的需求，因为大模型通信那里面是带着历史信息的。
        geshu = len(self.status_list)
        if geshu>0:
            # 那就是没毛病，可以正常取
            status_jieguo = copy.deepcopy(self.status_list[-1])
            if geshu>self.min_list_num:
                # 如果不是太少，就删去一些时效性差的。
                del self.status_list[0]
        else:
            status_jieguo = ""

        return status_jieguo

    def run_mul(self):
        # 跟socket那个里面一样，需要启动新的线程一直跑着的东西放在这里面。

        # 这里面的逻辑应该是：不管外面是怎么操作，这里面就固定的念完一句再念最新的一句。
        # 然后生成和念也还是异步的。生成就是用最新的态势来生成，和大模型的互动也是算作生成的一部分。
        # 存态势也是异步的，存态势是跟外面同步的，外面一步这里就存一个。
        #         
        self.thread1 = threading.Thread(target=self.run_generate)
        self.thread2 = threading.Thread(target=self.run_single_play)
        
        # 这个就不要什么扩展性了，因为这个结构是固定的
        self.thread1.start()
        self.thread2.start()
        pass

    def run_generate(self):
        # 正如socket通信肯定是异步的一样，大模型解说这里也肯定是异步的。
        # 这个应该持续地生成出pcm音频文件。
        while True:
            # 这个就是和大模型不断地互动，不断地生成出东西
            self.index_generate = self.index_generate + 1

            # 取态势
            status_str = self.pop_status_list()
            if status_str == "":
                # 那就是没有
                time.sleep(1)
                continue
            all_str = status_str + "\n 请给出解说词。" 

            # 和大模型交互
            response_str = self.model_communication.communicate_with_model(all_str)

            # 生成新的音频
            # 先生成一个新的位置
            name_new = r"jieshuo"+str(self.index_generate) + ".pcm"
            self.TTS_generator.set_pcm_name(name_new)
            # self.TTS_generator.auto_test_location
            # 然后来生成，生成完了看起来就完事儿了呗。
            TTS.text_to_voice(response_str)
            self.pcm_name_list.append(name_new)

    
    def run_play(self):
        # 这个是用来播放的，得思考一下播放的触发条件。
        geshu_generated = len(self.pcm_name_list)

        # 就先进先出呗？有的话就放，没有的话就等会儿。
        if geshu_generated>0:
            self.TTS_generator.display_voice(self.TTS_generator.auto_test_location, self.pcm_name_list[0])
            # 用完就可以删了.
            del self.pcm_name_list[0]
        else:
            # 那就是列表里没得可说，那就先放一下。
            time.sleep(1)
        pass 

    def __del__(self):
        # 我猜这个不写也不会咋样
        self.thread1.join()
        self.thread2.join()

def main_loop_demo():
    shishi_TTS = TTS_interface()
    shishi_TTS.run_mul()
    text_demo_list = get_text_demo_list()
    for i in range(len(text_demo_list)):
        text_demo_single = text_demo_list[i]
        time.sleep(1.5)
        TTS_interface.add_status_list(text_demo_single)
    pass 

def get_text_demo_list():
    # 这个是用于测试的，生成一个list用于实现持续地往里面喂东西。
    text_demo_list = [] 
    text_demo_list.append("一个幽灵，共产主义的幽灵，在欧洲游荡。为了对这个幽灵进行神圣的围剿，旧欧洲的一切势力，教皇和沙皇、梅特涅和基佐、法国的激进派和德国的警察，都联合起来了。")
    text_demo_list.append("资产阶级抹去了一切向来受人尊崇和令人敬畏的职业的神圣光环。它把医生、律师、教士、诗人和学者变成了它出钱招雇的雇佣劳动者。资产阶级撕下了罩在家庭关系上的温情脉脉的面纱，把这种关系变成了纯粹的金钱关系。")
    text_demo_list.append("但是，资产阶级不仅锻造了置自身于死地的武器；它还产生了将要运用这种武器的人——现代的工人，即无产者。")
    text_demo_list.append("共产党人不屑于隐瞒自己的观点和意图。他们公开宣布：他们的目的只有用暴力推翻全部现存的社会制度才能达到。让统治阶级在共产主义革命面前发抖吧。无产者在这个革命中失去的只是锁链。他们获得的将是整个世界。")
    text_demo_list.append("如是我闻。一时佛在舍卫国祗树给孤独园，与大比丘众千二百五十人俱。尔时世尊，食时著衣持钵，入舍卫大城乞食。于其城中次第乞已，还至本处，饭食讫，收衣钵，洗足已，敷座而坐。")
    text_demo_list.append("时长老须菩提在大众中，即从座起，偏袒右肩，右膝著地，合掌恭敬。而白佛言：「希有！世尊。如来善护念诸菩萨，善付嘱诸菩萨。世尊！善男子、善女人，发阿耨多罗三藐三菩提心，云何应住？云何降伏其心？」佛言：「善哉！善哉！须菩提！如汝所说，如来善护念诸菩萨，善付嘱诸菩萨。汝今谛听，当为汝说。善男子、善女人，发阿耨多罗三藐三菩提心，应如是住，如是降伏其心。」「唯然！世尊！愿乐欲闻。」")
    text_demo_list.append("佛告须菩提：「诸菩萨摩诃萨，应如是降伏其心：所有一切众生之类-若卵生、若胎生、若湿生、若化生；若有色、若无色；若有想、若无想；若非有想非无想，我皆令入无馀涅盘而灭度之。如是灭度无量无数无边众生，实无众生得灭度者。何以故？须菩提！若菩萨有我相、人相、众生相、寿者相，即非菩萨。」")
    text_demo_list.append("复次：「须菩提！菩萨於法，应无所住，行於布施。所谓不住色布施，不住声、香、味、触、法布施。须菩提！菩萨应如是布施，不住於相。何以故？若菩萨不住相布施，其福德不可思量。须菩提！於意云何？东方虚空可思量不？」「不也，世尊！」「须菩提！南、西、北方、四维、上、下虚空，可思量不？」「不也。世尊！」「须菩提！菩萨无住相布施，福德亦复如是，不可思量。须菩提！菩萨但应如所教住！」")
    text_demo_list.append("「须菩提！於意云何？可以身相见如来不？」「不也，世尊！不可以身相得见如来。何以故？如来所说身相，即非身相。」佛告须菩提：「凡所有相，皆是虚妄。若见诸相非相，即见如来。」")   
    text_demo_list.append("鸣大钟一次！推动杠杆，启动活塞和泵。鸣大钟两次！按下按钮，发动引擎，点燃涡轮，注入生命。鸣大钟三次！齐声歌唱，赞美万机之神！")   
    text_demo_list.append("Night gathers, and now my watch begins. It shall not end until my death. I shall take no wife, hold no lands, father no children. I shall wear no crowns and win no glory. I shall live and die at my post. I am the sword in the darkness. I am the watcher on the walls. I am the fire that burns against the cold, the light that wakes the sleepers, the shield that guards the realms of men. I pledge my life and honor to the Night's Watch, for this night, and all the nights to come.")

    return text_demo_list


if __name__ == "__main__":
    print("当朝大学士，统共有五位")