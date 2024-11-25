# 这个是一个单纯的调试工具，原则上不会用到任何真正运行的场合。
# 功能是提供一系列的接口，确保能够原样代替其他的socket文件，用于调试。确切地说是隔离这部分然后调试别的部分。
import socket
import threading
import time
import os.path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from socket_communication.socket_base import socket_base
from PySide6 import QtCore

class socket_debug(QtCore.QThread):
    def __init__(self, dialog_box=None,ip="0.0.0.0",port="114514"):
        QtCore.QThread.__init__(self)
        self.dialog_box = dialog_box
        self.status_str = "socket_debug"
        self.flag_human_interact = False
        pass
    
    def run_mul(self):
        pass