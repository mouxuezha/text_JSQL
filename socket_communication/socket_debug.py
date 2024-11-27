# 这个是一个单纯的调试工具，原则上不会用到任何真正运行的场合。
# 功能是提供一系列的接口，确保能够原样代替其他的socket文件，用于调试。确切地说是隔离这部分然后调试别的部分。
import socket
import threading
import time
import os.path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from socket_communication.socket_base import socket_base
from PySide6 import QtCore
import random

class socket_debug(QtCore.QThread):
    def __init__(self, dialog_box=None,ip="0.0.0.0",port="114514"):
        QtCore.QThread.__init__(self)
        self.dialog_box = dialog_box
        self.status_str = "socket_debug"
        self.flag_human_interact = False
        self.flag_new = False
        pass
    
    def run_mul(self):
        # 这个是用来开多线程的。原则上只要我启动接收线程之后不对齐，就不会卡主线程。
        # 原则上，需要多个socket的话就在这里面开一堆多线程，然后标一下序号啥的，反正都简单
        self.thread1 = threading.Thread(target=self.run_single)
        # self.thread1 = threading.Thread(target=self.run_single_debug)

        self.thread1.start()

        print("socket_debug ready")

        # thread1.join()

        pass
    
    def run_single(self):
        # 这个是个用于调试的，刷新一下收到的态势可也。
        while(True):
            self.received_str = "socket_debug.run_single, received_str updated.\n" + "我方需要攻取位于经纬度坐标(100.1247, 13.6615)的夺控点，将陆战装备移动到夺控点处并消灭夺控点附近敌人可占领夺控点，地图范围为经度100.0923到100.18707，纬度范围为13.6024到13.6724，导弹发射车不能机动。地图大部分为陆地，具有河流、桥梁和路网，在经纬度坐标(100.137,13.644),(100.116,13.643)(100.164,13.658)有可供步兵占领和建立防线的建筑物。" + str(random.randint(0,114514))
            self.status_str = self.received_str
            self.flag_new = True
            time.sleep(1)
        pass

    def send_str(self,status_str:str):
        print("socket_debug.send_str: "+status_str)
        time.sleep(1)
        pass

    def receive_str(self):
        self.received_str = "socket_debug.receive_str received.\n" + "我方需要攻取位于经纬度坐标(100.1247, 13.6615)的夺控点，将陆战装备移动到夺控点处并消灭夺控点附近敌人可占领夺控点，地图范围为经度100.0923到100.18707，纬度范围为13.6024到13.6724，导弹发射车不能机动。地图大部分为陆地，具有河流、桥梁和路网，在经纬度坐标(100.137,13.644),(100.116,13.643)(100.164,13.658)有可供步兵占领和建立防线的建筑物。" + str(random.randint(0,114514))
        self.status_str = self.received_str
        self.flag_new = True
        time.sleep(1)
        return self.received_str