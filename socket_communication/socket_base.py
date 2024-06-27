# 写着发现socket_server和socket_client的代码基本一致，可以考虑合并通用部分。让结构阳间一点。


import socket
import threading
import time

class socket_base():
    def __init__(self,socket_type="server"):
        # 这个应该是一个封装好的、不卡主线程的东西，随时能够用它发字符串，随时能读取它收的字符串、随时能知道新收到的字符串有没有被读取过了。


        self.flag_new = False
        self.received_str = ""
        self.sended_str = ""
        self.flag_new = False # 暴力一点，这个用来标识有没有收到新的
        self.flag_send = False # 这个是标识发没发
        self.socket_type = socket_type

        self.__init_socket()
        pass 

    def __init_socket(self):
        # 初始化socket
        self.real_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # 这个是本地的。等到真的通信的话要用别的
        host = socket.gethostname()
        port = 12345
        
        if self.socket_type == "server":
            # 服务端
            self.real_socket.bind((host, port))
            self.real_socket.listen(1)   
            
            print("等待连接...")
            self.client_socket, self.client_address = self.real_socket.accept()
            print("连接地址:", self.client_address)
        elif self.socket_type == "client":
            # 客户端
            self.real_socket.connect((host, port))
            self.client_socket=self.real_socket
            pass 
        
        print("socket init ready")     

    
    def send_str(self,status_str:str):
        # 这个就是发字符串的。现阶段怎么快怎么来，什么延迟啊那些一概先不管。
        print('连接地址：', self.client_socket)

        self.client_socket.send(status_str.encode('utf-8'))
        pass 
    
    def receive_str(self):
        # 这个是用来接收字符串的。
        new_received_str = self.client_socket.recv(4096).decode('utf-8')
        
        # 判断一下是不是收重了，都是好事儿
        if new_received_str != self.received_str:
            self.received_str = new_received_str
            self.flag_new = True
        else:
            self.flag_new = False

        return self.received_str
    
        pass 
    def load_config(self):
        # 加载配置文件
        config_name = "config.txt"
        with open(config_name, "r") as f:
            config_str = f.readlines()
            host = config_str[0]
            port = config_str[1]
        
        return host, port
