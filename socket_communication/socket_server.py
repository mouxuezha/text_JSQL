# 这个是用来整一个服务器端，到时候跟决胜千里平台跑在同一个电脑上的。客户端服务器只跑dialog_box

import socket

class socket_server():
    def __init__(self):
        # 这个应该是一个封装好的、不卡主线程的东西，随时能够用它发字符串，随时能读取它收的字符串、随时能知道新收到的字符串有没有被读取过了。
        self.__init_socket()
        pass 

    def __init_socket(self):
        # 初始化socket
        self.real_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host = socket.gethostname()
        port = 12345

        self.real_socket.bind((host, port))
        self.real_socket.listen(1)   
        print("socket_server ready")     
        print("等待客户端连接...")
        client_socket, client_address = self.real_socket.accept()
        print("连接地址:", client_address)
    
    def send_str(self,status_str):
        # 这个就是
        pass 
    
    def run_mul(self):
        # 这个是用来开多线程的。原则上只要我启动接收线程之后不对齐，就不会卡主线程。
        # 原则上，需要多个socket的话就在这里面开一堆多线程，然后标一下序号啥的，反正都简单
        pass

    def run_single(self):
        # 这个是用来跑死循环的。死死呗。
        pass