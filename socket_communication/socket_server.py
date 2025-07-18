# 这个是用来整一个服务器端，到时候跟决胜千里平台跑在同一个电脑上的。客户端服务器只跑dialog_box

import socket
import threading
import time
import os.path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from socket_communication.socket_base import socket_base
from PySide6 import QtCore

class socket_server(socket_base, QtCore.QThread):
    def __init__(self,dialog_box = None,ip="0.0.0.0",port="114514",player="red"):
        # 这个应该是一个封装好的、不卡主线程的东西，随时能够用它发字符串，随时能读取它收的字符串、随时能知道新收到的字符串有没有被读取过了。
        socket_base.__init__(self,"server",ip=ip,port=port)
        QtCore.QThread.__init__(self)
        self.dialog_box = dialog_box
        self.flag_new = False # 暴力一点，这个用来标识有没有收到新的
        self.flag_send = False # 这个是标识发没发

    def run_mul(self):
        # 这个是用来开多线程的。原则上只要我启动接收线程之后不对齐，就不会卡主线程。
        # 原则上，需要多个socket的话就在这里面开一堆多线程，然后标一下序号啥的，反正都简单
        self.thread1 = threading.Thread(target=self.run_single)
        # self.thread1 = threading.Thread(target=self.run_single_test)


        print("socket_server ready")

        # thread1.join()
        pass

    def run_single_test(self):
        # 这个是用来跑死循环的。死死呗。持续保持接收
        i=0
        while True:
            i= i+1 
            time.sleep(1)
            
            print('这里是server，连接地址：', self.real_socket)

            status_str = '这个是服务器发来的第{}条态势'.format(i)
            self.send_str(status_str)
            time.sleep(1)
            received_str = self.receive_str()
            print(received_str)
        
        self.client_socket.close()
        pass
    
    def run_single(self):
        # 这个是用来和一个server端dialog_box类似物来协作的。
        self.flag_new = False # 暴力一点，这个用来标识有没有收到新的
        self.flag_send = False # 这个是标识发没发                
        while True:
            time.sleep(0.01)
            print('这里是服务器，连接地址：', self.real_socket)
            command_str = self.receive_str()
            # 专门处理一下那边按按钮传过来的命令
            if command_str == '客户端命令：开始推演':
                # 那就说明是点了按钮了
                self.dialog_box.p.start()
                # self.config["flag_server_waiting"] == False # 换了一种方式去时实现
            elif command_str == '客户端命令：结束推演':
                # 那就说明是点了按钮了
                self.dialog_box.p.terminate()
                # self.config["flag_server_waiting"] == True # 换了一种方式去时实现
            if self.flag_new == True:
                self.dialog_box.flag_order_renewed = True
                self.dialog_box.reset_all(0.01)
                print("服务器收到客户端的命令：", command_str)
            
            if self.dialog_box.flag_order_renewed == True:
                # 人类改过命令，所以这里要给它传过去。# 客户端的话这个不怎么触发。
                self.flag_send = True
                command_str = self.dialog_box.order_now
                self.send_str(command_str)
                self.dialog_box.flag_order_renewed = False

        pass

    def __del__(self):
        self.thread1.join()

class socket_server_2player(QtCore.QThread):
    # 搞一个服务于2玩家的东西。
    def __init__(self, config:dict, dialog_box = None,**kargs):
        QtCore.QThread.__init__(self)
        if "model" in kargs:
            self.model=kargs["model"]
        else:
            self.model = "debug" # "normal"

        if self.model == "debug":
            print("attension: socket_server_2player running in debug model, only 1 socket connection established")

        self.red_server = socket_base("server",ip=config["red_ip"],port=config["red_port"])
        if self.model == "normal":
            self.blue_server = socket_base("server",ip=config["blue_ip"],port=config["blue_port"])
            print("socket_server_2player running in normal model, 2 socket connections established")
        self.dialog_box = dialog_box
        self.flag_new = False # 暴力一点，这个用来标识有没有收到新的
        self.flag_send = False # 这个是标识发没发


    def run_single(self):
        # 这个是用来和一个server端dialog_box类似物来协作的。
        self.flag_new = False # 暴力一点，这个用来标识有没有收到新的
        self.flag_send = False # 这个是标识发没发                
        while True:
            time.sleep(0.5)
            # print('红方玩家连接地址：', self.red_server.real_socket)
            # if self.model == "normal":
            #     print('蓝方玩家连接地址：', self.blue_server.real_socket)
            red_command_str = self.red_server.receive_str() # 这个设定就是公平器件，得两边都下了指令之后，服务器才对其进行一起处理。
            if self.model == "normal":
                blue_command_str = self.blue_server.receive_str()
            else:
                blue_command_str = '客户端命令：开始推演'

            # red_command_str, blue_command_str = self.human_intervene_check()
            # 专门处理一下那边按按钮传过来的命令
            if (red_command_str == '客户端命令：开始推演') or (blue_command_str == '客户端命令：开始推演'):
                # 那就说明是点了按钮了.两个都开始那就是真的开始了
                # self.dialog_box.p.start()
                self.dialog_box.p.config["flag_server_waiting"] == False # 换了一种方式去时实现
                # 我草，写成双等号都能好使？解锁了奇怪的知识。
            elif (red_command_str == '客户端命令：结束推演') or (blue_command_str == '客户端命令：结束推演'):
                # 一样的，两个都结束了那就是真的结束了。
                # self.dialog_box.p.terminate()
                self.dialog_box.p.config["flag_server_waiting"] == True # 换了一种方式去时实现

            if self.red_server.flag_new == True:
                self.dialog_box.flag_order_renewed = True
                self.red_server.flag_new = False
                print("服务器收到红方玩家命令：", red_command_str)
                self.red_server.received_str = red_command_str # 这个更新的好像不太正确，来一波逃避可耻但有用。

            if self.model == "normal":
                if self.blue_server.flag_new == True:
                    self.dialog_box.flag_order_renewed = True
                    # self.dialog_box.reset_all(0.01)
                    self.blue_server.flag_new = False
                    print("服务器收到蓝方玩家命令：", blue_command_str)         
                    self.blue_server.received_str = blue_command_str     
            
            if self.dialog_box.flag_order_renewed == True:
                # 人类改过命令，所以这里要给它传过去。两个都传，这才叫健全。
                # server这头的态势是要分发到所有玩家去的去的。
                self.flag_send = True
                command_str = self.dialog_box.order_now
                self.red_server.send_str(command_str)
                if self.model == "normal":
                    self.blue_server.send_str(command_str)
                self.dialog_box.flag_order_renewed = False

        pass

    def run_single2(self,server_single:socket_base):
        # 这个是升级一下搞成更加阳间的架构，命令随发随执行，然后分成红蓝两方各自一个线程的。
        # 只开red的前提下，它应该跟run_single是一样的。
        # 这个是用来和一个server端dialog_box类似物来协作的。
        self.flag_new = False # 暴力一点，这个用来标识有没有收到新的
        self.flag_send = False # 这个是标识发没发 

        while True:
            time.sleep(0.5)
            oneside_command_str = server_single.receive_str() # 这个设定就是公平器件，得两边都下了指令之后，服务器才对其进行一起处理。

            # red_command_str, blue_command_str = self.human_intervene_check()
            # 专门处理一下那边按按钮传过来的命令
            # 这里得改一下逻辑，一个开始就是就是开始，两个结束才是结束。搞点逻辑运算符，不然开不起来了
            if (oneside_command_str == '客户端命令：开始推演'):
                # 那就说明是点了按钮了.两个都开始那就是真的开始了
                # self.dialog_box.p.start()
                self.dialog_box.p.config["flag_server_waiting"] = \
                self.dialog_box.p.config["flag_server_waiting"] and False # 换了一种方式去时实现
            elif (oneside_command_str == '客户端命令：结束推演'):
                # 一样的，两个都结束了那就是真的结束了。
                # self.dialog_box.p.terminate()
                self.dialog_box.p.config["flag_server_waiting"] = \
                    self.dialog_box.p.config["flag_server_waiting"] and True # 换了一种方式去时实现

            if server_single.flag_new == True:
                self.dialog_box.flag_order_renewed = True
                server_single.flag_new = False
                print("服务器收到一方玩家命令：", oneside_command_str)
                server_single.received_str = oneside_command_str # 这个更新的好像不太正确，来一波逃避可耻但有用。
         
            if self.dialog_box.flag_order_renewed == True:
                # 人类改过命令，所以这里要给它传过去。两个都传，这才叫健全。
                # server这头的态势是要分发到所有玩家去的去的。
                self.flag_send = True
                command_str = self.dialog_box.order_now
                server_single.send_str(command_str)
                self.dialog_box.flag_order_renewed = False

    def run_mul(self):
        # 这个是用来开多线程的。原则上只要我启动接收线程之后不对齐，就不会卡主线程。
        # 原则上，需要多个socket的话就在这里面开一堆多线程，然后标一下序号啥的，反正都简单
        # self.thread1 = threading.Thread(target=self.run_single)
        # # self.thread1 = threading.Thread(target=self.run_single_test)

        # self.thread1.start()

        # 新的，真的实现了多线程的。
        self.thread1 = threading.Thread(target=self.run_single2,args = (self.red_server,))
        self.thread2 = threading.Thread(target=self.run_single2,args = (self.blue_server,))

        self.thread1.start()
        self.thread2.start()


        print("socket_server ready")

        # thread1.join()
        pass

    def human_intervene_check(self):
        # check一下远处发过来的是啥。以及发没发。

        # 一个偷懒的方案是：不check标志位了，而是检测字符串看里面有没有特定的标志
        red_response_str = self.red_server.received_str
        
        if ("玩家指令" in red_response_str) :
            # 那就是红方玩家给过来的是指令
            # print("human_intervene_check，红方命令："+red_response_str)
            pass
        elif ("客户端命令" in red_response_str) :
            pass
        else:
            red_response_str = "" # 来个空的，防止报错
        
        if self.model == "normal":
            blue_response_str = self.blue_server.received_str
            if ("玩家指令" in blue_response_str) :
                # # 那就是蓝方玩家对应的服务器进程收到东西了。那就读出来。
                # # blue_response_str = self.blue_server.receive_str()
                # blue_response_str = self.blue_server.received_str
                # print("human_intervene_check，蓝方命令："+blue_response_str)
                pass
            else:
                blue_response_str = "" # 来个空的，防止报错
        else:
                blue_response_str = "调试网络通信，蓝方不要命令。" # 来个空的，防止报错
        

        return red_response_str, blue_response_str
    
    def send_to_players(self,status_str):
        # 统一一下接口，这个是给客户端分发态势信息或者别的信息的。应该保证输入这里面的玩意能发出去。
        # 先来个最挫的堵塞版的。
        self.red_server.send_str(status_str)
        if self.model == "normal":
            self.blue_server.send_str(status_str)
        self.flag_send = True

    def send_to_players2(self, status_list:list):
        # 进一步的统一接口，搞一个兼容红蓝方分别发态势的东西
        status_str_red = status_list[0]
        status_str_blue = status_list[1]

        self.red_server.send_str(status_str_red)
        if self.model == "normal":
            self.blue_server.send_str(status_str_blue)
        self.flag_send = True

                
if __name__ == "__main__":
    server = socket_server(dialog_box=None,ip="192.168.1.117",port="20001")
    server.run_mul()