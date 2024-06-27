# 这个是预备在客户端上的，也是接收、发信息

import socket
import threading
import time
import os.path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from socket_communication.socket_base import socket_base

class socket_client(socket_base):
    def __init__(self):
        super().__init__("client")
        pass

    def run_mul(self):
        # 这个是用来开多线程的。原则上只要我启动接收线程之后不对齐，就不会卡主线程。
        # 原则上，需要多个socket的话就在这里面开一堆多线程，然后标一下序号啥的，反正都简单
        thread1 = threading.Thread(target=self.run_single)

        thread1.start()

        print("socket_client ready")

        thread1.join()

        pass

    def run_single(self):
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

if __name__ == '__main__':
    client = socket_client()
    client.run_mul()