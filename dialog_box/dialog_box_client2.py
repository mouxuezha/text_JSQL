# 这个是基于dialog_box_client，通过socket在远程开了一个窗口，而且这个窗口是要跟Qt那里的前端进行对接的。原则上功能应该是一样的，收态势、发命令，和人互动。

import os.path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from socket_communication.socket_client import socket_client
from socket_communication.Env import *
import argparse

from main import command_processor

import random
import time 
import threading

from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtWidgets import QDialog 

class MyWidget(): # 这里就先不显示窗口了，原则上应该就不用继承那个了。
    def __init__(self, role="red_player",**kargs):
        self.order_now = "none"
        self.status_str = "none"
        self.flag_order_renewed = False

        self.step_num = 0
        self.p_status ="off"
        self.p = command_processor(self,role=role, config=kargs["config"])  # 和大模型交互的通信在这里面实现了。
        self.socket_client = self.p.socket_client # 看看能不能偷个懒
        self.socket_client.run_mul() # 试一下放这里行不行。在这里原则上还没有结束init呢

        self.__init_net()
        self.__init_env()


    def __init_env(self):
        self.max_episode_len = self.net_args.max_episode_len
        # self.env = Env(self.net_args.ip, self.net_args.port)
        self.env = Env_server(self.net_args.ip, self.net_args.port)
        

    def __init_net(self):
        parser = argparse.ArgumentParser(description='Provide arguments for agent.')
        parser.add_argument("--ip", type=str, default="127.0.0.1", help="Ip to connect")
        # parser.add_argument("--ip", type=str, default="192.168.43.93", help="Ip to connect")
        parser.add_argument("--port", type=str, default=30001, help="port to connect")
        parser.add_argument("--epochs", type=int, default=200, help="Number of training epochs to run")  # 设置训练轮次数
        parser.add_argument("--max-episode-len", type=int, default=3000, help="maximum episode length")
        net_args = parser.parse_args()
        self.net_args = net_args
        return net_args     

    def run_mul(self):
        # 这个由于传态势到QT和传命令到服务器是异步的，所以这里不能搞阻塞的事情了。
        # 原则上可以用类似唐燃哥Qt里那种直接connect的机制实现，但是从自主可控的角度，宁愿傻逼点，写点能看懂能改明白的。

        self.env.init_socket()

        # 准确的说，这里面开了三个进程，一个转发态势，一个转发命令，一个command_process
        thread1 = threading.Thread(target=self.status_single)
        thread2 = threading.Thread(target=self.command_single)  
        thread3 = threading.Thread(target=self.run_main_loop_client)  
        
        # 然后就启动线程呗
        thread1.start()
        thread2.start()
        # self.p_status = "on"
        # self.p.start()
        thread3.start()
        

        # 然后就等待线程结束呗
        thread1.join()
        thread2.join()
        thread3.join()
        
        # 然后就返回结果呗

        pass

    def run_main_loop_client(self):
        # 这个是包装一下，用于从Qthread迁移到Python自带的多线程的。因为现在不需要信号槽机制但是需要断点调试了。
        # 哎，还是调试工具不够、水平没玩明白。
        self.p.main_loop_client()

    def status_single(self):
        while(True):
            # 把收到的态势拿出来，刷到Qt那里面去。这个道理上和那边到底收没收成功是无关的
            status_str_received = self.socket_client.status_str
            # status_str_received = self.socket_client.receive_str()

            # 由于是异步的，这里不能再检查这个了，不然刷没了。
            # if self.socket_client.flag_new == True:

            print("status_single: status_str_received = " + status_str_received)

            self.env.send_str(status_str_received)

            time.sleep(0.5) # 没有任何的必要一直刷刷刷，差不多就行了，加一下这个，控制一下速度。

    def command_single(self):
        while(True):
            # 从Qt那边把命令收过来，然后更新到command process里面。
            receiver_str = self.env.receive_str()
            # self.env.receive_str()这里面已经判断过一次是不是收重了，所以直接拿来用就行了。
            self.flag_order_renewed = self.env.flag_new # 标志位不要一直刷，理想的是那边点一下，这边只进一次大模型。
            if self.flag_order_renewed:
                # 如果没有收重，而是确实是新的，那就更新一下
                self.order_now = receiver_str
                print("command_single:receiver_str from QtC++"+receiver_str)
                # 把命令从env里取出来之后要把标志位改回去，不然就会一直刷。
                self.env.reset_str()

                flag_exit,flag_start = self.check_start_and_exit(receiver_str)
                if flag_exit:
                    # 检测到就关了这个功能到时候是不是实装还有待考虑。其实关后台不是一个好的选择
                    print("command_single: flag_exit="+str(flag_exit))
                    self.socket_client.send_str(receiver_str)
                    
                if flag_start:
                    print("command_single: flag_start="+str(flag_start))
                    # 检测到这个就直接把命令发过去算了，往python服务器那里去发。
                    self.socket_client.send_str(receiver_str)

            time.sleep(0.5) # 没有任何的必要一直刷刷刷，差不多就行了，加一下这个，控制一下速度。
            pass
    def command_used(self):
        # 命令用过之后调一下这个。清理内存、重置标志位，之类的。
        self.flag_order_renewed = False
        self.order_now = ""
        print("command_used, reset human intent")

    def get_status_str(self,status_str, step_num):
        # 这个本来是带界面的时候用来改前端显示的字的，这里不带界面了那就无所谓了奥
        pass 

    def get_status_from_socket(self, status_str):
        self.status_str = status_str

    def reset_all(self,time_delay=0.01):
        # 这个也是带界面的时候用来刷新显示的，这里不带界面了那就无所谓了奥。
        # 不过标志位还是得改一下。
        self.command_used()

        pass

    def check_start_and_exit(self, order_new):
        # 这个的目的很单纯，就是检测一下进来的是不是退出命令。是就返回true
        flag_exit = False
        flag_start = False
        if "客户端命令：结束推演" in order_new:
            # 那就说明进来的是退出命令，
            flag_exit = True
        else:
            flag_exit = False

        if "客户端命令：开始推演" in order_new:
            # 那就说明进来的是退出命令，
            flag_start = True

        return flag_exit,flag_start

if __name__ == "__main__":
    # 跑起来看看成色

    config = {"red_ip":"192.168.1.115", "red_port": "20001",
            "blue_ip": "192.168.1.115", "blue_port": "20002", 
            "dialog_box_model": "QtC++","socket_debug_model":"net_debug"}    # dialog_box_model能选QtC++和QtPython，socket_debug_model有local_debug和net_debug，区别是用不用那个假的socket类。
    # 这个config其实是服务于command_processor的，不是服务于dialogbox，所以原则上其他的dialogbox也可以用。
    
    widget = MyWidget(role="red_player",config = config)
    widget.run_mul()