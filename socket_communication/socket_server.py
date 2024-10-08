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

        self.thread1.start()

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
            elif command_str == '客户端命令：结束推演':
                # 那就说明是点了按钮了
                self.dialog_box.p.terminate()
            if self.flag_new == True:
                self.dialog_box.flag_order_renewed = True
                self.dialog_box.reset_all(0.01)
                print("服务器收到客户端的命令：", command_str)
            
            if self.dialog_box.flag_order_renewed == True:
                # 人类改过命令，所以这里要给它传过去。
                self.flag_send = True
                command_str = self.dialog_box.order_now
                self.send_str(command_str)
                self.dialog_box.flag_order_renewed = False

        pass

    def __del__(self):
        self.thread1.join()

class socket_server_2player(QtCore.QThread):
    # 搞一个服务于2玩家的东西。
    def __init__(self, config:dict, dialog_box = None):
        QtCore.QThread.__init__(self)
        self.red_server = socket_base("server",ip=config["red_ip"],port=config["red_port"])
        self.blue_server = socket_base("server",ip=config["blue_ip"],port=config["blue_port"])
        self.dialog_box = dialog_box
        self.flag_new = False # 暴力一点，这个用来标识有没有收到新的
        self.flag_send = False # 这个是标识发没发


    def run_single(self,server):
        # 这个是用来和一个server端dialog_box类似物来协作的。
        self.flag_new = False # 暴力一点，这个用来标识有没有收到新的
        self.flag_send = False # 这个是标识发没发                
        while True:
            time.sleep(0.01)
            print('红方玩家连接地址：', self.red_server.real_socket)
            print('蓝方玩家连接地址：', self.blue_server.real_socket)
            red_command_str = self.red_server.receive_str()
            blue_command_str = self.blue_server.receive_str()
            # 专门处理一下那边按按钮传过来的命令
            if (red_command_str == '客户端命令：开始推演') and (blue_command_str == '客户端命令：开始推演'):
                # 那就说明是点了按钮了.两个都开始那就是真的开始了
                self.dialog_box.p.start()
            elif (red_command_str == '客户端命令：结束推演') and (blue_command_str == '客户端命令：结束推演'):
                # 一样的，两个都结束了那就是真的结束了。
                self.dialog_box.p.terminate()

            if self.red_server.flag_new == True:
                self.dialog_box.flag_order_renewed = True
                self.dialog_box.reset_all(0.01)
                print("服务器收到红方玩家命令：", red_command_str)
            if self.blue_server.flag_new == True:
                self.dialog_box.flag_order_renewed = True
                self.dialog_box.reset_all(0.01)
                print("服务器收到蓝方玩家命令：", blue_command_str)                
            
            if self.dialog_box.flag_order_renewed == True:
                # 人类改过命令，所以这里要给它传过去。两个都传，这才叫健全。
                # server这头的态势是要分发到所有玩家去的去的。
                self.flag_send = True
                command_str = self.dialog_box.order_now
                self.red_server.send_str(command_str)
                self.blue_server.send_str(command_str)
                self.dialog_box.flag_order_renewed = False

        pass

    def run_mul(self):
        # 这个是用来开多线程的。原则上只要我启动接收线程之后不对齐，就不会卡主线程。
        # 原则上，需要多个socket的话就在这里面开一堆多线程，然后标一下序号啥的，反正都简单
        self.thread1 = threading.Thread(target=self.run_single)
        # self.thread1 = threading.Thread(target=self.run_single_test)

        self.thread1.start()

        print("socket_server ready")

        # thread1.join()
        pass

    def human_intervene_check(self):
        # check一下远处发过来的是啥。以及发没发。
        if self.red_server.flag_new == True:
            # 那就是红方玩家对应的服务器进程收到东西了。那就读出来。
            red_response_str = self.red_server.receive_str()
        else:
            red_response_str = "" # 来个空的，防止报错

        if self.blue_server.flag_new == True:
            # 那就是蓝方玩家对应的服务器进程收到东西了。那就读出来。
            blue_response_str = self.blue_server.receive_str()
        else:
            blue_response_str = "" # 来个空的，防止报错

        return red_response_str, blue_response_str
if __name__ == "__main__":
    server = socket_server(dialog_box=None,ip="192.168.1.117",port="20001")
    server.run_mul()