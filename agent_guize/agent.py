# 这个是agent.py先占着位置，用于把程序的其他地方调好。

import math
import copy
import numpy as np
import codecs
import sys, os
import xlrd
import time
from enum import Enum
from base_agent import BaseAgent
import queue

class Agent(BaseAgent):
    def __init__(self, name="Red") -> None:
        self.num = 0
        self.status = {}
        self.commands_queue = queue.Queue(maxsize=114514)
        # 这层维护一个命令队列，可能会比较好。每条命令应该有退出机制，退出之后删了。
        pass

    def get_status(self):
        print("get_status unfinished yet, using status_demo")
        status_demo = {}
        status_demo['unit_type'] = "MainBattleTank"
        status_demo['x'] = 27.5
        status_demo['y'] = 27.5
        status_demo['altitude'] = 100

        return status_demo
    
    def set_commands(self, commands):
        for i in range(len(commands)):
            self.commands_queue.put(commands[i])
        pass 

    def reset(self):
        self.num = 0
    
    def deploy(self):
        print("deploy unfinished yet, using status_demo")
        pass 

    def step(self, status):
        print("deploy unfinished yet, using status_demo")
        pass
        
