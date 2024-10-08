# 这个是预备在客户端上的，也是接收、发信息

import socket
import threading
import time
import os.path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from socket_communication.socket_base import socket_base
from PySide6 import QtCore

class socket_client(socket_base,QtCore.QThread):
    def __init__(self, dialog_box=None,ip="0.0.0.0",port="114514"):
        socket_base.__init__(self,"client",ip=ip,port=port)
        QtCore.QThread.__init__(self)
        self.dialog_box = dialog_box
        self.status_str = ""
        self.flag_human_interact = False
        pass

    def run_mul(self):
        # 这个是用来开多线程的。原则上只要我启动接收线程之后不对齐，就不会卡主线程。
        # 原则上，需要多个socket的话就在这里面开一堆多线程，然后标一下序号啥的，反正都简单
        self.thread1 = threading.Thread(target=self.run_single)
        # self.thread1 = threading.Thread(target=self.run_single_debug)

        self.thread1.start()

        print("socket_client ready")

        # thread1.join()

        pass

    def run_single_debug(self):
        # 这个是用来跑死循环的。死死呗。
        self.flag_new = False # 暴力一点，这个用来标识有没有收到新的
        self.flag_send = False # 这个是标识发没发
        i = 0 
        while True:
            i= i+1

            print('这里是客户端，连接地址：', self.real_socket)

            time.sleep(1)
            # 发送
            command_send = "这个是客户端发送的命令，第" + str(i) + "条"
            self.real_socket.send(command_send.encode('utf-8'))
            time.sleep(0.01)
            # 接收
            # data = self.real_socket.recv(4096)
            data_str = self.receive_str()
            print("客户端收到服务端的信息：", data_str)       

        self.client_socket.close()
        pass
    
    def run_single(self):
        self.flag_new = False # 暴力一点，这个用来标识有没有收到新的
        self.flag_send = False # 这个是标识发没发        
        while True:
            time.sleep(0.01)
            print('这里是客户端，连接地址：', self.real_socket)
            status_str = self.receive_str()
            
            if self.flag_new == True:
                self.dialog_box.flag_order_renewed = True
                self.dialog_box.reset_all(0.01)
                self.dialog_box.get_status_str(status_str,0)
                print("客户端收到服务端的态势：", status_str)
                self.status_str = status_str
            
            if self.dialog_box.flag_order_renewed == True:
                # 人类改过命令，所以这里要给它传过去。
                self.flag_send = True
                command_str = self.dialog_box.order_now
                self.send_str(command_str)
                self.dialog_box.flag_order_renewed = False

    def __del__(self):
        self.thread1.join()                

if __name__ == '__main__':
    client = socket_client(dialog_box=None,ip="192.168.1.117",port="20001")
    client.run_mul()