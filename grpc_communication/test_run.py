import time
from grpc_client_lib import GRPCClientManager
import argparse
from env import AgentEnv
from env import PlatformEnv
import time
#import numpy as np
import re
import collections
import random



def main():
    # 创建客户端管理器
    manager = GRPCClientManager()
    
    try:
        # 创建3个连接：2个基于data_act.proto，1个基于data.proto
        # 假设三个连接指向不同的服务端地址，实际使用时替换为真实地址
        client1 = manager.create_data_act_client("169.254.64.50:30001")  # data_act连接1
        client2 = manager.create_data_act_client("169.254.64.50:30002")  # data_act连接2
        client3 = manager.create_data_client("169.254.64.50:50005")     # data连接
        
        # 连接服务器
        if not client1.connect():
            print("客户端1连接失败")
            return
            
        if not client2.connect():
            print("客户端2连接失败")
            return
            
        if not client3.connect():
            print("客户端3连接失败")
            return
        
        redEnv = AgentEnv(client1)
        blueEnv = AgentEnv(client2)
        platformEnv = PlatformEnv(client3)
        

        Episode=10000
        for ep in range(Episode):
            print("================ {} th =============".format(ep))
            platformEnv.Reset()
            plat_timesteps = 0
            done_mask=0
            while True:
                redact = []
                blueact = []
                redaction = {"Action": redact}
                blueaction = {"Action": redact}   
                redstate = redEnv.get_states()
                bluestate = blueEnv.get_states()


                if plat_timesteps >= 0:  
                    #act.append({"Type": "Launch", "Id": "warhead0","Lon": 124.5, "Lat": 18.28,"MissileType":1}) 
                    redact.append({"Type": "Launch", "Id": "Truck0","Lon": 125, "Lat": 18.28,"MissileType":0}) 
                    redact.append({"Type": "Launch", "Id": "Truck0","Lon": 125.1, "Lat": 18.28,"MissileType":0}) 
                    # redact.append({"Type": "Launch", "Id": "Truck0","Lon": 125.2, "Lat": 18.28,"MissileType":0}) 
                    # redact.append({"Type": "Launch", "Id": "Truck0","Lon": 125.3, "Lat": 18.28,"MissileType":0}) 
                    # redact.append({"Type": "Launch", "Id": "Truck0","Lon": 125.4, "Lat": 18.28,"MissileType":0}) 
                redEnv.Act(redaction)
                blueEnv.Act(blueaction)
                platformEnv.Step()        
                plat_timesteps += 1

                time.sleep(1)
                if plat_timesteps == 10:
                    break

            
    except KeyboardInterrupt:
        print("用户中断程序")
    finally:
        print("关闭所有连接")
        manager.shutdown_all()

if __name__ == "__main__":
    main()