# 从劳动竞赛抄到test_scene又抄到这里了，虽然都是socket，但是这里开一个可以区别于我之前写的那些，结构好一些。

# coding=UTF-8
from __future__ import division
import socket
import numpy as np

SIZE = 1024 * 1024*2
import json
import os

class Env():
    def __init__(self, IP, port):
        # 这个是client的写法，其实是有问题的。和唐燃哥对了一下是我python这边当server端，就别搞那种0.5秒刷一次的事情了，确实要阳间一些。
        self._ip = IP
        self._port = port
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
        self.client.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, SIZE)
        self.client.connect((self._ip, self._port))
        # print("connect success")
        if os.path.exists("message.txt"):
            os.unlink("message.txt")
    
    def _recv(self):
        result = self.client.recv(SIZE)
        result = result.decode(encoding="utf-8")
        while 1:
            num_lcount = result.count('{')
            num_rcount = result.count('}')
            if num_lcount == num_rcount:
                break
            result1 = self.client.recv(SIZE)
            result1 = result1.decode(encoding="utf-8")
            result = result + result1

        # 粘包处理
        if result.count("}{") != 0:
            pos = result.rfind("}{")
            result = result[pos + 1:]
        dataBuffer = list()
        for i in range(result.count("}{")):
            pos = result.find("}{")
            dataStr = result[0:pos + 1]
            result = result[pos + 1:]
            dataBuffer.append(dataStr)
        dataBuffer.append(result)
        # tail = tail.decode(encoding="utf-8")
        return dataBuffer[0]
    
    def _send(self, message):
        try:
            # print("send", message)
            self.client.send(str(message).encode('utf-8'))
            result = self._recv()
            # print("recv", result) # 这个关了，不然满屏输出乱七八糟，抓不到重点了
            # with open("message.txt", "a+") as f:
            #     f.write("========================\n")
            #     f.write("agent send:\n")
            #     f.write(message)
            #     f.write("\n")
            #     f.write("agent recv:\n")
            #     f.write(result)
            #     f.write("\n")
            return result
        except:
            print("socket error,{} not send".format(str(message)))
    
    def GetCurrentStatus(self):
        # 这个是发消息问那边要JSON的，尽量和原来的保持一致。
        command = {"CMD": "GetCurrentStatus"}
        command = json.dumps(command)
        statusinfo = self._send(command)
        return statusinfo
    
    def GetHumanIntent(self):
        # 这个是发消息给问那边要人类意图的
        command = {"CMD": "HumanIntent"}
        command = json.dumps(command)
        statusinfo = self._send(command)
        return statusinfo

    def Step(self, Action=None):
        # 这个也是直接复用就好了，反正都是一行一行的命令发过去就行了，鉴定为可也。
        command = {"CMD": "Step"}
        if Action != None:
            command.update(Action)
        command = json.dumps(command)
        result = self._send(command)
        return result

# class Env_server():
#     def __init__(self,IP, port) -> None:
#         self.set_IP_and_port(IP, port)
#         self.received_str = "None"
#         pass
#     def set_IP_and_port(self,IP,port):
#         # 这个还是跑不了的，设定一下自己到底是什么IP什么端口号。
#         # TODO：讲道理后期应该整成扫描的，把局域网里面的所有端口号都扫一遍那种。
#         self.IP = IP
#         self.port = port
#         self.flag_local_host = False
#         pass 

#     def init_socket(self):
#         # 初始化socket。这个放在init里面就会一直卡着，感觉不是太理想。
#         self.real_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
#         # 服务端
#         self.real_socket.bind((self.IP, self.port))
#         self.real_socket.listen(1)   
            
#         print("等待连接...")
#         # 这里是阻塞的，比较抽象
#         self.client_socket, self.client_address = self.real_socket.accept()
#         print("连接地址:", self.client_address)
        
#         print("socket init ready")    

#     def send_str(self,status_str:str):
#         # 这个就是发字符串的。现阶段怎么快怎么来，什么延迟啊那些一概先不管。
#         # print('连接地址：', self.client_socket)

#         self.client_socket.send(status_str.encode('utf-8'))
#         pass 
    
#     def receive_str(self):
#         # 这个是用来接收字符串的。任何时候调这个，总能读取出东西来。至于说是不是新的，得从标志位来看。
#         # 按照目前这个写法，标志位只保持一帧。
#         new_received_str = self.client_socket.recv(4096).decode('utf-8')
#         # print("new_received_str in receive_str:"+new_received_str)
#         # 经过测试，这个就是堵塞的，不发一次收一次这个线程就不会接着往下走。
        
#         # 判断一下是不是收重了，都是好事儿
#         if new_received_str != self.received_str:
#             self.received_str = new_received_str
#             # print(self.received_str)
#             self.flag_new = True
#         else:
#             self.flag_new = False

#         return self.received_str
    
#     def reset_str(self):
#         # 主要是清一清标志位和收到的字符串啥的。
#         self.flag_new = False
#         # self.received_str =""# 这个不能清了，不然比较就失效了。

class Env_server():
    def __init__(self,IP, port, seat = "commandor") -> None:
        self.set_IP_and_port(IP, port)
        self.received_str = "None"
        self.seat = seat
        pass
    def set_IP_and_port(self,IP,port):
        # 这个还是跑不了的，设定一下自己到底是什么IP什么端口号。
        # TODO：讲道理后期应该整成扫描的，把局域网里面的所有端口号都扫一遍那种。
        self.IP = IP
        self.port = port
        self.flag_local_host = False
        pass 

    def init_socket(self):
        # 初始化socket。这个放在init里面就会一直卡着，感觉不是太理想。
        self.real_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # 服务端
        self.real_socket.bind((self.IP, self.port))
        self.real_socket.listen(1)   
            
        print("等待连接...")
        # 这里是阻塞的，比较抽象
        self.client_socket, self.client_address = self.real_socket.accept()
        print("连接地址:", self.client_address)
        
        print("socket init ready")    

    def send_str(self,status_str:str):
        # 这个就是发字符串的。现阶段怎么快怎么来，什么延迟啊那些一概先不管。
        print('连接地址：', self.client_socket)

        self.client_socket.send(status_str.encode('utf-8'))
        pass 
    
    def receive_str(self):
        # 这个是用来接收字符串的。任何时候调这个，总能读取出东西来。至于说是不是新的，得从标志位来看。
        # 按照目前这个写法，标志位只保持一帧。
        new_received_str = self.client_socket.recv(32768).decode('utf-8')
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
