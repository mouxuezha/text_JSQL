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

        # 准确的说，这里面开了三个进程，一个转发态势，一个转发命令，一个command_process
        thread1 = threading.Thread(target=self.status_single)
        thread2 = threading.Thread(target=self.command_single)  
        # 然后就启动线程呗
        thread1.start()
        thread2.start()
        self.p_status = "on"
        self.p.start()
        

        # 然后就等待线程结束呗
        thread1.join()
        thread2.join()
        # 然后就返回结果呗

        pass

    def status_single(self):
        
        # 把收到的态势拿出来，刷到Qt那里面去。
        status_str_received = self.socket_client.status_str

        self.env.send_str(status_str_received)

        time.sleep(0.5) # 没有任何的必要一直刷刷刷，差不多就行了，加一下这个，控制一下速度。

    def command_single(self):
        # 从Qt那边把态势收过来，然后更新到command process里面。
        receiver_str = self.env.receive_str()
        # self.env.receive_str()这里面已经判断过一次是不是收重了，所以直接拿来用就行了。
        self.flag_order_renewed = self.env.flag_new
        if self.flag_order_renewed:
            # 如果没有收重，而是确实是新的，那就更新一下
            self.order_now = receiver_str
        time.sleep(0.5) # 没有任何的必要一直刷刷刷，差不多就行了，加一下这个，控制一下速度。
        pass

if __name__ == "__main__":
    # 跑起来看看成色

    config = {"red_ip":"192.168.1.140", "red_port": "20001",
            "blue_ip": "192.168.1.140", "blue_port": "20002", 
            "dialog_box_model": "QtC++","socket_debug_model":"local_debug"}    # dialog_box_model能选QtC++和QtPython，socket_debug_model暂时只有local_debug
    
    widget = MyWidget(role="red_player",config = config)
    widget.run_mul()