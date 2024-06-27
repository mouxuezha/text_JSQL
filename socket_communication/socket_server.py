# 这个是用来整一个服务器端，到时候跟决胜千里平台跑在同一个电脑上的。客户端服务器只跑dialog_box

import socket
import threading
import time
import os.path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from socket_communication.socket_base import socket_base

class socket_server(socket_base):
    def __init__(self):
        # 这个应该是一个封装好的、不卡主线程的东西，随时能够用它发字符串，随时能读取它收的字符串、随时能知道新收到的字符串有没有被读取过了。
        super().__init__("server")

    def run_mul(self):
        # 这个是用来开多线程的。原则上只要我启动接收线程之后不对齐，就不会卡主线程。
        # 原则上，需要多个socket的话就在这里面开一堆多线程，然后标一下序号啥的，反正都简单
        thread1 = threading.Thread(target=self.run_single)

        thread1.start()

        print("socket_server ready")

        thread1.join()
        pass

    def run_single(self):
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


if __name__ == "__main__":
    server = socket_server()
    server.run_mul()