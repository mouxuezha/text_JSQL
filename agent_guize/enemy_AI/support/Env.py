# coding=UTF-8
from __future__ import division
import socket
import numpy as np

SIZE = 1024 * 1024*2
import json
import random
import re
import os
import os.path
import sys
waimian_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
waimian_path = os.path.join(waimian_path, '..')
waimian_path = os.path.join(waimian_path, '..') # 笨是笨一点，但总之退出去了。也就调试的时候用一下。
sys.path.insert(0, waimian_path)
from grpc_communication.grpc_client_lib import *
from grpc_communication.env import AgentEnv
from grpc_communication.env import PlatformEnv

class Env():
    def __init__(self, Env_config={"red_ip":"169.254.64.50","red_port":"30001","blue_ip":"169.254.64.50","blue_port":"40001","control_ip":"169.254.64.50","control_port":"50005"}):
        manager = GRPCClientManager()
        red_str = Env_config["red_ip"] + ":"+Env_config["red_port"]
        print("redstr: ", red_str)
        red_client = manager.create_data_act_client(red_str)  # data_act连接1

        blue_str = Env_config["blue_ip"] + ":"+Env_config["blue_port"]
        print("bluestr: ", blue_str)
        blue_client = manager.create_data_act_client(blue_str)  # data_act连接2
        
        # manager = GRPCClientManager()
        control_str = Env_config["control_ip"] + ":"+Env_config["control_port"]
        control_client = manager.create_data_client(control_str)
        print("  ENV INIT  测试客户端是否创建完成  ")
        if not red_client.connect():
            raise Exception("红方grpc连接失败")
            
        if not blue_client.connect():
            raise Exception("蓝方grpc连接失败")
            
        if not control_client.connect():
            raise Exception("控制grpc连接失败")
        


        self.redEnv = AgentEnv(red_client)
        self.blueEnv = AgentEnv(blue_client)
        self.platformEnv = PlatformEnv(control_client)


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

    def Step(self, Action={"red_action":[],"blue_action":[]}):  # 尽量保持和之前的接口和含义一致，尽量能兼容之前的东西。
        # ？？？谁给我注了的？注了那玩个毛

        action_red = {"Action":Action["red_action"]}
        self.redEnv.Act(action_red)
        
        action_blue = {"Action":Action["blue_action"]}
        self.blueEnv.Act(action_blue)

        result = self.platformEnv.Step() 
        
        return result

    def Reset(self):
        result = self.platformEnv.Reset() # 这个本来有返回值的，但是分析认为没有也不为大害，因此也就罢了。
        return result

    def Save(self):
        result = self.platformEnv.Save()
        return result

    def Load(self, filename=None):
        self.platformEnv.Load(filename)

    def GetCurrentStatus(self):
        red_statusinfo = self.redEnv.GetCurrentStatus()
        blue_statusinfo = self.blueEnv.GetCurrentStatus()
        return red_statusinfo,blue_statusinfo

    def GetWeaponInfo(self):
        weaponinfo = self.platformEnv.GetWeaponInfo()
        return weaponinfo

    def SetSimInterval(self, timestep):
        self.platformEnv.SetSimInterval(timestep)

    def SetRender(self, render=True):
        # self.platformEnv.SetRender(render)
        print("SetRender: 这玩意就没实际用过，鉴定为寄")

    def GetCurrentResult(self):
        # result = self.platformEnv.GetCurrentResult()
        print("Env.GetCurrentResult: 这接口目前还没有")
        # print("GetCurrentResult OK")
        result = {"blueScore":"0","redScore":"0"}
        # result =str(result)
        return result

    def GetPisResult(self):
        command = {"CMD": "GetPisResult"}
        command = json.dumps(command)
        result = self._send(command)
        # print("GetPisResult OK")
        return result

    def statusparser(self, result):
        # print(result)
        if result is not None:
            status = json.loads(result)
            # status = json.loads(json.loads(result)["status"])
            # redState = status["redState"]
            # blueState = status["blueState"]
            jieguo = status
        else:
            jieguo = {}
            print("statusparser received None")
        return jieguo

    def GetLandForm(self,lon,lat):
        command = {"CMD": "GetCurrentPlatform"}
        command.update({"lon": lon,"lat":lat})
        command = json.dumps(command)
        result = self._send(command)
        # print("result")
        # print("GetLandForm OK")
        return result

    def resultparser(self, result):
        #print(result)
        if "status" not in json.loads(result).keys():
            return None
        if result.find('status') < 0:
            return None
        if json.loads(result)["status"] == "":
            return None
        status = json.loads(json.loads(result)["status"])
        redState = status["redState"]
        blueState = status["blueState"]
        return redState, blueState

    def reward(self):
        result = self.GetCurrentStatus()
        if json.loads(result)["status"] == "":
            return None
        status = json.loads(json.loads(result)["status"])
        return status

    def Terminal(self):
        command = {"CMD": "Terminal"}
        command = json.dumps(command)
        result = self._send(command)
        if json.loads(result) == "":
            return None
        result = json.loads(result)
        return result
    def SetRedRecvScene(self):
        command = {"CMD": "RedReceiveSence"}
        command = json.dumps(command)
        result = self._send(command)
        # print("GetPisResult OK")
        return result
    
    def SetBlueRecvScene(self):
        command = {"CMD": "BlueReceiveSence"}
        command = json.dumps(command)
        result = self._send(command)
        # print("GetPisResult OK")
        return result   
    
    def get_state(self):
        raise Exception("Env.get_state: unfinished yet.")
    
class Env_demo():
    def __init__(self, Env_config={"red_ip":"169.254.64.50","red_port":"30001","blue_ip":"169.254.64.50","blue_port":"40001","control_ip":"169.254.64.50","control_port":"50005"}):
        # 这东西存在的意义只是为了调试的时候不报错。
        print("Env_demo initialized for debug.")
        pass 

    def Reset(self):
        return {"0":0} 

    def Step(self, Action):
        return {"0":0} 

    def SetRender(self, render=True):
        pass 

    def GetCurrentResult(self):
        return {"0":0} 
    
    def GetCurrentStatus(self):
        return {"0":0} 
    
    def statusparser(self, result):
        return None, None