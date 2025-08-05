import json
import os.path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from grpc_communication.grpc_client_lib import GRPCClientManager 

SIZE = 1024 * 1024 * 4
import json
import random
import re
import time
import atexit


class AgentEnv():
    def __init__(self, client):
        self.client = client

    def _act_recv(self):
        msg = self.client.get_received_message(timeout=0.5)
        if msg:
            print(f"客户端1主动获取: {msg}")

    def _act_send(self, message):
        print("_act_send:",message)
        self.client.send_message(message)

    def Act(self, Action=None):
        command = {"CMD": "Action"}
        if Action != None:
            command.update(Action)
        command = json.dumps(command)
        self._act_send(command)
        return

    def GetCurrentStatus(self):
        command = {"CMD": "GetCurrentStatus"}
        command = json.dumps(command)
        statusinfo = self._act_send(command)
        
        # # 调试用的延时程序
        # n_try = 1145 
        # while((len(self.client.request_queue.queue)==0) and n_try>0):
        #     time.sleep(0.1)
        #     n_try = n_try-1
        
        statusinfo = self.client.get_received_message(timeout=1)
        if(statusinfo is None):
            print("getCurrentStatus: status info is none")
            print(statusinfo)
            return
        print(statusinfo)

        # 这段补不明觉厉，感觉没啥意义。且待原作者子航鉴定一下再删。
        # if "status" in statusinfo:
        #     return statusinfo
        # else:
        #     statusinfo = self._act_send(command)
        return statusinfo

    def statusparser(self, result):
        if result is None:
            return None
        if "status" not in json.loads(result).keys():
            return None
        if json.loads(result)["status"] == "":
            return None
        status = json.loads(json.loads(result)["status"])
        
        State = status
        return State

    def get_states(self):
        result = self.GetCurrentStatus()
        # while (self.statusparser(result) == None):
        #     result = self.GetCurrentStatus()
        state = self.statusparser(result)
        return state

class PlatformEnv():
    def __init__(self, client):
        self.client = client

    def _control_recv(self):
        msg = self.client.get_received_message(timeout=10)
        if msg:
            print(f"客户端1主动获取: {msg}")

    def _control_send(self, message):
        print("_control_send:",message)
        self.client.send_message(message)
        msg = self.client.get_received_message(timeout=10)
        return msg

    def _send(self,msg):
        raise Exception("_send: disabled here")

    # 设置消息接收回调函数
    def on_message_received(client_name, message):
        print(f"客户端{client_name}收到消息: {message}")

    def Step(self, Action=None):
        command = {"CTRL": "Step"}
        command = json.dumps(command)
        print(command)
        result = self._control_send(command)
        return result

    def Reset(self):
        command = {"CTRL": "Reset"}
        command = json.dumps(command)
        jieguo = self._control_send(command)
        return jieguo

    def Save(self):
        command = {"CTRL": "Save"}
        command = json.dumps(command)
        self._control_send(command)

    def Load(self, filename=None):
        command = {"CTRL": "Load"}
        if filename != None:
            command.update({"fileName": filename})
        command = json.dumps(command)
        self._control_send(command)



    def LoadMap(self, fileName=None):
        command = {"CTRL": "Setmap"}
        if fileName != None:
            command.update({"fileName": fileName})
        command = json.dumps(command)
        self._control_send(command)

    def _act_send(self, message):
        print("_act_send:",message)
        self.client.send_message(message)

    def SetSimInterval(self, timestep):
        command = {"CMD": "SetSimInterval"}
        SetSimInterval = {"siminterval": timestep}
        command.update(SetSimInterval)
        command = json.dumps(command)
        self._control_send(command)
        # print("SetSimInterval OK")

    def statusparser(self, result):
        if "status" not in json.loads(result).keys():
            return None
        if json.loads(result)["status"] == "":
            return None
        status = json.loads(json.loads(result)["status"])
        
        State = status
        return State


class Env():
    def __init__(self, client):
        self.client = client

    def _act_recv(self):
        msg = self.client.get_received_message(timeout=0.5)
        if msg:
            print(f"客户端1主动获取: {msg}")

    def _act_send(self, message):
        self.client.send_message()
    
    def _send(self,msg):
        raise Exception("_send: disabled here")
    
    # 设置消息接收回调函数
    def on_message_received(client_name, message):
        print(f"客户端{client_name}收到消息: {message}")

    def Step(self, Action=None):
        command = {"CTRL": "Step"}
        command = json.dumps(command)
        print(command)
        result = self._control_send(command)
        return result

    def Act(self, Action=None):
        command = json.dumps(Action)
        self._act_send(command)
        result = self._act_recv()
        return result

    def Reset(self):
        command = {"CTRL": "Reset"}
        command = json.dumps(command)
        self._control_send(command)

    def Save(self):
        command = {"CTRL": "Save"}
        command = json.dumps(command)
        self._control_send(command)

    def Load(self, filename=None):
        command = {"CTRL": "Load"}
        if filename != None:
            command.update({"fileName": filename})
        command = json.dumps(command)
        self._control_send(command)



    def LoadMap(self, fileName=None):
        command = {"CTRL": "Setmap"}
        if fileName != None:
            command.update({"fileName": fileName})
        command = json.dumps(command)
        self._control_send(command)



    def GetCurrentStatus(self):
        command = {"CMD": "GetCurrentStatus"}
        command = json.dumps(command)
        self._act_send(command)
        statusinfo = self.client.get_received_message(timeout=10)
        if(statusinfo is None):
            print("getCurrentStatus: status info is none")
        if "status" in statusinfo:
            return statusinfo
        else:
            statusinfo = self._send(command)
        return statusinfo

    def GetWeaponInfo(self):
        command = {"CMD": "GetWeaponInfo"}
        command = json.dumps(command)
        weaponinfo = self._act_send(command)
        print("GetWeaponInfo OK")
        return weaponinfo

    def SetSimInterval(self, timestep):
        command = {"CMD": "SetSimInterval"}
        SetSimInterval = {"siminterval": timestep}
        command.update(SetSimInterval)
        command = json.dumps(command)
        self._control_send(command)
        # print("SetSimInterval OK")

    def SetRender(self, render=True):
        command = {"CMD": "SetRender"}
        command.update({"render": render})
        command = json.dumps(command)
        self._act_send(command)

    def GetCurrentResult(self):
        command = {"CMD": "GetCurrentResult"}
        command = json.dumps(command)
        result = self._act_send(command)
        print("GetCurrentResult OK")
        return result
        

    def GetPisResult(self):
        command = {"CMD": "GetPisResult"}
        command = json.dumps(command)
        result = self._act_send(command)
        # print("GetPisResult OK")
        return result

    def statusparser(self, result):
        if "status" not in json.loads(result).keys():
            return None
        if json.loads(result)["status"] == "":
            return None
        status = json.loads(json.loads(result)["status"])
        redState = status["redState"]
        blueState = status["blueState"]
        return redState, blueState