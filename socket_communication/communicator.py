# 这个是从test_decision里面弄来的相对阳间一点的通信类

import os.path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from socket_communication.Env import *
# from mission_arrange.mission_arrange import mission_arrange
from text_transfer.text_transfer import text_transfer
from text_transfer.stage_prompt import StagePrompt
import argparse, queue, time,threading
from concurrent.futures import ThreadPoolExecutor
import time
from abc import ABC, classmethod ,abstractmethod

class yanshi_comunicator(ABC):
    # 还是那个路数，开个进程一直转着，看GUI那头有什么东西发过来。发过来的先缓存着，然后每隔一段时间处理一次。
    # 意图识别、调用不同函数的，在这里面先做一个比较拉但是能用的。后面如果要好的，再说。
    def __init__(self) -> None:
        
        self.__init_envs()
        self.__init_seat()
        
        self.flag_init = True # 这个用来标记当前是不是第一步。
        self.flag_debug = False
        self.config_dict = {}
        
        self.config_dict["flag_exit"] = False # 这个用来标志运行中是不是需要退出了

        
        self.text_transfer = text_transfer()

        self.commands_queue = queue.Queue(114514)
        self.send_queue = queue.Queue(114514) # 干脆上来先打好基础，发送的专门整个消息队列好了，不然不是就乱了嘛。
        # 感叹一句，再往下是不是就要来线程锁什么的了。
        self.receive_queue = queue.Queue(114514) # 接收过来的先不解析，先存着一下。
        # 直接快进一波，直接快进到线程池处理各种handle。
        self.handle_threadpool = ThreadPoolExecutor(max_workers=10)
        
        self.running_result = {} # 这个用来存那些个运行出来的中间结果，都是“有就用现成的，没有就现算一个或者没有就现读取一个”的逻辑
        self.running_result["Planning"] = []
        pass

    def __init_envs(self):
        self.env_dict = {} 
        self.net_args = self.__init_net(ip = "127.0.0.1", port = 30001)
        self.max_episode_len = self.net_args.max_episode_len
        print("auto_run_comunicator: 绑定席位和IP地址...")
        env_single = Env_server(self.net_args.ip, self.net_args.port,seat="commandor") # 开这个，就是和图形用户界面交互
        # env_single = Env_server_debug(self.net_args.ip, self.net_args.port,seat="commandor") # 开这个，就是本质上不和图形用户界面交互。
        self.env_dict["commandor"] = env_single
        print("__init_envs: unfinished yet")


    def __init_net(self,ip = "127.0.0.1", port = 30001):
        parser = argparse.ArgumentParser(description='Provide arguments for agent.')
        parser.add_argument("--ip", type=str, default="127.0.0.1", help="Ip to connect")
        # parser.add_argument("--ip", type=str, default="192.168.43.93", help="Ip to connect")
        parser.add_argument("--port", type=str, default=port, help="port to connect")
        parser.add_argument("--epochs", type=int, default=200, help="Number of training epochs to run")  # 设置训练轮次数
        parser.add_argument("--max-episode-len", type=int, default=3000, help="maximum episode length")
        net_args = parser.parse_args()
        # self.net_args = net_args
        return net_args        
    
    def __init_seat(self):
        # 分席位的处理也是在这里处理一下算了。原则上只需要跑这一个后端python，是有机会把分席位的事情都干了的。有几分劳动竞赛那个对战的意思了，但是要防止像当时那样来回修改和屎山化。各方比较好接受的是前端大哥们写，然后我能改多少改点儿。
        self.seat_access = {} 
        self.seat_access["status"] = ["态势评估"] # 态势情报席位
        self.seat_access["support"] = ["装备编辑","子任务编辑","历史方案"] # 信息支援席位
        self.seat_access["commandor"] = ["root"] # 指挥控制席位，完全权限。
        self.seat_access["evaluator"] = ["方案编辑","方案评估"] # 方案评估席位
        pass
    
    def run_mul(self):
        # 和之前类似，这个就是开起来跑着就好的多线程不阻塞的
        for env in self.env_dict.values():
            env.init_socket()
        
        thread1 = threading.Thread(target=self.run_single_receive)
        thread2 = threading.Thread(target=self.run_single_send)
        thread3 = threading.Thread(target=self.run_single_handle)

        # 然后就启动线程呗
        thread1.start()
        thread2.start()    
        thread3.start()

        print("auto_run_communicator: successfully started, wuhu, qifei")    

        # 主进程得整个东西看住了，不然主进程直接结束了反而别的就结束了。现在这个是主进程了。
        # thread1.join()
        # thread2.join()
        # thread3.join()
        # 换个方案，允许强制退出。
        flag_temp = True
        while(flag_temp):
            time.sleep(1.14514)
            print("auto_run_communicator:running...")

            # self.send_response("{\"SchemesDataList\":[],\"msgCommid\":\"测试接受数据Ai指令\"}" +"text str from auto_run_communicator")
            # self.send_response("{\"SchemesDataList\":[],\"msgCommid\":\"text str from auto_run_communicator\"}")
            # self.send_response(self.text_transfer.response_wrap("text str from auto_run_communicator")) # 鉴定为好使。
            if self.config_dict["flag_exit"] == False:
                # 那就是无事发生。
                pass
            else:
                # 那就是从某处得到了要退出的说法，那就退出。
                flag_temp = False
        pass 

    def run_single_receive(self):
        # 这个是单线程的，无限循环写在这里面。
        while(True):
            time.sleep(1.14514)
            for seat in self.env_dict.keys():
                gui_order_str = self.env_dict[seat].receive_str() # 所有席位的全都收一遍。
                # 从方便调试的角度考虑，接收进来应该先放队列，然后再统一处理
                gui_order_dict = {seat:gui_order_str}
                self.receive_queue.put(gui_order_dict)

                # 从方便调试的角度：
                print("received: " + gui_order_str)

        pass

    def run_single_send(self):
        # 这个是单线程的，无限循环写在这里面。
        while(True):
            time.sleep(1.14514)
            if not self.send_queue.empty():
                send_str = self.send_queue.get()
                for seat in self.env_dict.keys():
                    self.env_dict[seat].send_str(send_str)
        pass

    def run_single_handle(self):
        # 这个是单线程的，无限循环写在这里面。
        # 这个是处理指令的
        while(True):
            # if (not self.receive_queue.empty()) or True : # 后面这半句and True是调试的时候用的。
            if (not self.receive_queue.empty()):
                
                # receive_dict_single = self.receive_queue.get() # 好家伙，这个会阻塞。pop不阻塞。
                # receive_str = list(receive_dict_single.values())[0]
                # receive_seat = list(receive_dict_single.keys())[0]
                
                # 这有一个逻辑缺陷，不get了之后它就会一直循环，所以还是得get。
                receive_dict_single = self.receive_queue.get()
                receive_str = list(receive_dict_single.values())[0]
                receive_seat = "commandor"
                
                # self.handle_command_expedient(receive_seat,receive_str)# 分别执行就完事了。
                # future = self.handle_threadpool.submit(self.handle_command_expedient,receive_seat,receive_str) 
                # 莲餐版本的展示。
                future = self.handle_threadpool.submit(self.handle_command_liancan,receive_seat,receive_str)

                # 这个和threading不一样了，这个不用打括号了。
                jieguo = future.result() # 猜测是得调用result的时候才会真的执行，所以只写上面那句不写这里这句的话它不太行

        
        # 这里搞个线程池。看起来就很丝滑了。任务调起来是一回事，执行成什么样子嘛再说可也
        pass
    # 其实可以考虑把整个handle都搞成虚函数，这样逻辑上更合理一点，
    @classmethod
    @abstractmethod
    def handle_command_liancan(self,seat="none",command="none"):
        pass

    def send_response(self,response_str:str):
        # 这次在后端就分开，显示的命令是显示的命令，增加点儿掌控力.这个是通用的入队列的说法。
        # 这里所谓发送，其实就是放进队列里面去的意思嘛。发回去的就不用分什么席位了。
        if not("SchemesDataList" in response_str):
            response_str = self.text_transfer.response_wrap(response_str)
            print("send_response: warning, invalide json, auto-fixed.")
        self.send_queue.put(response_str)
        pass 

    def send_plan(self,new_plans:list):
        # 把多方案解析解析，给GUI发过去。
        
        # 然后把方案弄出来,然后准备发过去。
        # plans_str = self.text_transfer.plan_list_to_str(new_plans)

        # self.running_result["Planning_str"] = plans_str
        # # 组合一下报文
        plans_str = self.text_transfer.plan_list_to_str2(new_plans)
        
        # 行吧，果然没有那么好的事情让别人照着我的数据结构来，那就怎么方便怎么来呗。
        self.send_response(plans_str)

        # 后面如果要有别的办法来传结构化数据，那就都是在这个函数里面拓展。

        pass
