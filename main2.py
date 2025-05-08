# 这个是整理一下之前的，实现单台电脑上的、使用雪楠哥他们前端的，人机交互

from dialog_box.dialog_box_server import MyWidget as MyWidget_server
from dialog_box.dialog_box_client2 import MyWidget as MyWidget_client
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtWidgets import QDialog 
from main import * 
from socket_communication.communicator import yanshi_comunicator

import threading,time 

class auto_run_comunicator():
    # 本来是早都该弄的了，自动化的启动器。那现在弄一下好了。
    def __init__(self):
        # 初始化一系列的通信啥的东西。
        self.config = {"red_ip":"127.0.0.1", "red_port": "31001",
                    "blue_ip": "127.0.0.1", "blue_port": "31002","flag_server_waiting":True,"dialog_box_model": "QtC++","socket_debug_model":"net_debug"}
        
        # 不能直接这么来，直接这么来就阻塞了。
        # self.__init_server()
        # self.__init_client_red()
        # self.__init_client_blue()

        # 原则上初始化完了就可以看着了，只要保证主线程不退出。
    
    def __init_server(self):
        print("init dialog_box_server")
        app = QtWidgets.QApplication([])
        config = self.config
        self.widget_server = MyWidget_server(config=config)
        self.widget_server.resize(800, 300)
        self.widget_server.show()        
        pass 

    def __init_client_red(self):
        time.sleep(1.14514)
        print("init dialog_box_client2 for red player")
        
        config = self.config    # dialog_box_model能选QtC++和QtPython，socket_debug_model有local_debug和net_debug，区别是用不用那个假的socket类。
        # 这个config其实是服务于command_processor的，不是服务于dialogbox，所以原则上其他的dialogbox也可以用。
        config["UI_port"] = 30002
        self.widget_red = MyWidget_client(role="red_player",config = config)
        self.widget_red.run_mul()        
        pass 
    
    def __init_client_blue(self):
        time.sleep(1.14514*2)
        print("init dialog_box_client2 for blue player")
        
        config = self.config    # dialog_box_model能选QtC++和QtPython，socket_debug_model有local_debug和net_debug，区别是用不用那个假的socket类。
        # 这个config其实是服务于command_processor的，不是服务于dialogbox，所以原则上其他的dialogbox也可以用。
        config["UI_port"] = 30003
        self.widget_blue = MyWidget_client(role="blue_player",config = config)

        self.widget_blue.run_mul()        
        pass 

    def run_mul(self):
        # 还得开多线程。不然建立连接那一步是阻塞的，直接就尬住了。
        thread1 = threading.Thread(target=self.__init_server)
        thread2 = threading.Thread(target=self.__init_client_red)  
        thread3 = threading.Thread(target=self.__init_client_blue)          
        
        # 然后就启动线程呗
        thread1.start()
        thread2.start()
        thread3.start()

        # 这个就是开一个主线程等着而已。既然如此那做一个命令行退出的东西可也。
        while(True):
            user_input = input("输入exit退出程序。")
            if user_input == "exit":
                break
            else:
                # 实际效果是输入错了就重新输。也留出后续扩展其他命令行功能的接口。
                pass

        pass

class liancan_runner(yanshi_comunicator):
    # 重新串一下流程可也。
    def __init__(self):
        # 先把需要初始化的东西初始化一下。
        super().__init__()

        self.Widget = MyWidget_debug() # 无人干预
        self.plan_interface = plan_interface()

        # self.config_dict = {} # 这里不用再写一次了，反而盖了

        self.plan_location_list = [] 
        self.threading_list = [] 
        # 这个就不能直接硬编码了，得从前面发东西过来看到底搞成什么样。还是收JSON就好了。
        # # plan_location_list.append(r"D:/EnglishMulu/test_decision/auto_test/新的/jieguo0.pkl")
        # # # plan_location_list.append(r"D:/EnglishMulu/test_decision/auto_test/jieguo1.pkl")
        # # # plan_location_list.append(r"D:/EnglishMulu/test_decision/auto_test/jieguo2.pkl")
        # shishi_interface.load_plans(plan_location_list) 
        # shishi_interface.set_plan(0) # 设定一下准备用哪个。         

        # 这个是单跑这个不跑dialog box，拟似人混，启动！
        # self.command_processor = command_processor(shishi_debug,flag_auto_CraftGame=False)
        # shishi.main_loop(role ="model3", plan_interface = shishi_interface)        
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
                # future = self.handle_threadpool.submit(self.handle_command_liancan,receive_seat,receive_str)
                # # 这个和threading不一样了，这个不用打括号了。
                # jieguo = future.result() # 猜测是得调用result的时候才会真的执行，所以只写上面那句不写这里这句的话它不太行 
                # # 傻逼吧，竟然是阻塞执行的？那要你何用
                # # future.add_done_callback(callback)
                self.handle_command_liancan(receive_seat,receive_str)
                # # 这里换一种多线程方式，然而换了就不对了，神奇。它们的内在逻辑还是不太一样
                # thread_single = threading.Thread(target=self.handle_command_liancan,args=(receive_seat,receive_str))
                # self.threading_list.append(thread_single)
                # self.threading_list[-1].start()

        
        # 这里搞个线程池。看起来就很丝滑了。任务调起来是一回事，执行成什么样子嘛再说可也
        pass
    # 其实可以考虑把整个handle都搞成虚函数，这样逻辑上更合理一点，
    def handle_command_liancan(self,seat="none",command="none"):
        # 这里要实现的功能还不少，选择方案、返回相应的文字、点一下开始推、返回子任务序列啥的。
        # 先来个教程，输出一些提示词，生成一个单个的方案，然后送到前端去。
        flag_pass, command_type = self.check_seat_expedient(seat,command) # 鉴权

        if flag_pass:
            # 那就没问题就进来了。
            if "选择方案" in command:
                # 那就是选择方案的分支，给过来的应该是个JSON，能解析出地址，或者至少是序号来
                self.handle_plan_select(seat,command)
            elif ("开始推演" in command) or ("结束推演" in command):
                self.handle_start(seat=seat,command=command)
        pass

    def handle_plan_select(self,seat="none",command="none"):
        # 选择方案，这个应该是个序号，然后去plan_interface里面找一下，返回一个方案。
        self.config_dict["selected_plan_index"] = 0 
        self.config_dict["selected_plan_location"] = 0 

        location = r"D:/EnglishMulu/test_decision/auto_test/新的/jieguo0.pkl" # 这个是默认的
        i = 0 
        for i in range(4):
            name_str = "方案"+str(i+1)
            if name_str in command:
                location = r"D:/EnglishMulu/test_decision/auto_test/jieguo"+str(0)+r".pkl"
                if os.path.exists(location):
                    # 那就是正常
                    self.send_response("已选定方案，可以开始推演。")
                else:
                    self.send_response("方案选择有误，已采用以前生成的方案。")
        self.plan_location_list.append(location)
        self.plan_interface.load_plans(self.plan_location_list)
        # print("handle_plan_select: unfinished yet. ")
        # self.send_response("已选定方案，可以开始推演。")
        
        # 这里再得搞一个给雪楠哥那边发个方案描述的的东西，用来填充描述。
        description_str = self.plan_interface.get_plan_description(i)
        self.send_response(description_str,model=2)

        pass

    def handle_start(self, seat="none",command="none"):
        # 那就开始推了，各种返回的东西都应该是在这里面去实现。至少每一帧返回现在的时间肯定是得要的。
        # try:
        #     # 这个得再开个线程。
        #     self.command_processor.main_loop(role ="model3", plan_interface = self.plan_interface)
        # except:
        #     str_output = "推演已经停止。"
        #     self.send_response(str_output)
        
        if command == "开始推演":
            # 莲餐版本的展示。
            # 先检测一下有没有设定好了方案的位置
            if len(self.plan_location_list)>0:
                # 那说明是对的
                future = self.handle_threadpool.submit(self.handle_run_JSQL,seat=seat,command=command)
                jieguo = future.result() 
                # 傻逼吧，竟然是阻塞执行的？那要你何用
                # future.add_done_callback(callback)

                # 这里换一种多线程方式，然而换了就不对了，神奇。它们的内在逻辑还是不太一样
                # thread_single = threading.Thread(target=self.handle_run_JSQL,args=(seat,command))
                # self.threading_list.append(thread_single)
                # self.threading_list[-1].start()

            else:
                self.send_response("无法启动推演，未正确设置方案路径")

        elif command == "结束推演":
            # # 这个就不用提交线程池了，一秒钟的事情。
            # self.handle_terminate(seat=seat,command=command)
            # 不然还是提一下好了，显得专业。
            future = self.handle_threadpool.submit(self.handle_terminate,seat=seat,command=command)
            jieguo = future.result() 
        pass

    def handle_run_JSQL(self, seat="none",command="none" ):
        self.command_processor = command_processor(self.Widget,flag_auto_CraftGame=True) # 得开线程池，不然写这里会阻塞。
        self.command_processor.set_communicator(self) # 把通信类的引用传进去。
        self.send_response("正在启动推演，请稍作等待。")
        time.sleep(1.14*5.14) 
        future = self.handle_threadpool.submit(self.command_processor.main_loop,role ="model3",plan_interface = self.plan_interface)
        jieguo = future.result() # 猜测是得调用result的时候才会真的执行，所以只写上面那句不写这里这句的话它不太行

    def handle_terminate(self, seat="none",command="none" ):
        # 这个就是把平台直接切了，原则上应该会直接结束那个线程。
        cmd_kill = "taskkill /IM CraftGameV1.exe -F"
        os.system(cmd_kill) # 还是这个靠谱，subprocess.Popen会报权限问题        
        str_output = "根据用户指令，已结束当前博弈推演。"
        self.send_response(str_output)

def callback(future):
    print("回调函数，试试",future.result())

if __name__ == "__main__":
    # 这个是用于配合演示的，另一个是用于配合开发的。
    # 确切地说，这个是用于配合红蓝方开了的那种实时人机融合决策的演示的。然后莲餐演示还得重新来过
    flag = 1
    if flag == 0 :
        shishi = auto_run_comunicator()
        shishi.run_mul()
    elif flag == 1:
        shishi = liancan_runner()
        shishi.run_mul()