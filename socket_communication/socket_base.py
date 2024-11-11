# 写着发现socket_server和socket_client的代码基本一致，可以考虑合并通用部分。让结构阳间一点。


import socket
import threading
import time

class socket_base():
    def __init__(self,socket_type="server",ip="0.0.0.0",port="114514"):
        # 这个应该是一个封装好的、不卡主线程的东西，随时能够用它发字符串，随时能读取它收的字符串、随时能知道新收到的字符串有没有被读取过了。


        self.flag_new = False
        self.received_str = ""
        self.sended_str = ""
        self.flag_new = False # 暴力一点，这个用来标识有没有收到新的
        self.flag_send = False # 这个是标识发没发
        self.socket_type = socket_type
        if port == "114514":
            # 那就说明没有设，那就本地直接来了。
            self.flag_local_host = True
        else:
            # 那就说明设置过了，那就按照设置过的来，局域网互联，岂不美哉。
            self.flag_local_host = False
            self.set_IP_and_port(ip,port)

        self.__init_socket()
        pass 

    def __init_socket(self):
        # 初始化socket
        self.real_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        if self.flag_local_host:
            # 这个是本地的。等到真的通信的话要用别的
            host = socket.gethostname()
            port = 12345
        else:
            host = self.my_ip
            port = int(self.my_port)
        
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
    
    def set_IP_and_port(self,IP,port):
        # 这个还是跑不了的，设定一下自己到底是什么IP什么端口号。
        # TODO：讲道理后期应该整成扫描的，把局域网里面的所有端口号都扫一遍那种。
        self.my_ip = IP
        self.my_port = port
        self.flag_local_host = False
        pass 



    
    def send_str(self,status_str:str):
        # 这个就是发字符串的。现阶段怎么快怎么来，什么延迟啊那些一概先不管。
        print('连接地址：', self.client_socket)

        self.client_socket.send(status_str.encode('utf-8'))
        pass 
    
    def receive_str(self):
        # 这个是用来接收字符串的。任何时候调这个，总能读取出东西来。至于说是不是新的，得从标志位来看。
        # 按照目前这个写法，标志位只保持一帧。
        new_received_str = self.client_socket.recv(4096).decode('utf-8')
        # print("new_received_str in receive_str:"+new_received_str)
        # 经过测试，这个就是堵塞的，不发一次收一次这个线程就不会接着往下走。
        
        # 判断一下是不是收重了，都是好事儿
        if new_received_str != self.received_str:
            self.received_str = new_received_str
            # print(self.received_str)
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
