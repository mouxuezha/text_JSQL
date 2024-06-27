# 这个是基于dialog_box，通过socket在远程开了一个窗口。原则上功能应该是一样的，收态势、发命令，和人互动。
import os.path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from socket_communication.socket_client import socket_client

import random
import time 

from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtWidgets import QDialog 

class MyWidget(QtWidgets.QWidget):
    step_signal = QtCore.Signal(int) # 这个用来刷新的，下一步把窗口里的所有东西都刷新一遍。
    # 所以在分客户端和本地的模式下，就是态势更新了就刷一下了，这个就得去socket_client里改了。
    # 后面考虑统一一下或者做个启动器。
    def __init__(self):
        super().__init__()

    
        self.order_now = "none"
        self.flag_order_renewed = False
        self.step_num = 0
        self.p_status ="off"
        # self.p = command_processor(self)
        self.socket_client = socket_client(self)
        

        self.button = QtWidgets.QPushButton("下达命令")
        self.button2 = QtWidgets.QPushButton("开始")
        self.text = QtWidgets.QLabel("小弈人混-人机互动界面",
                                     alignment=QtCore.Qt.AlignCenter)
        # self.dialog = QtWidgets.QDialog()
        self.dialog =  QtWidgets.QLineEdit("在此处输入人类作战意图，并点击按钮下达指令...")
        self.reset_all()


        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.text)
        self.layout.addWidget(self.dialog)
        self.layout.addWidget(self.button)
        self.layout.addWidget(self.button2)

        # 然后是定义信号和槽相关的内容，没几个所以不另开函数了
        self.button.clicked.connect(self.renew_order)
        # self.step_signal = QtCore.Signal(int) # 这个用来刷新的，下一步把窗口里的所有东西都刷新一遍。
        self.step_signal[int].connect(self.update_all) 
        self.button2.clicked.connect(self.click_button)

        self.socket_client.run_mul() # 试一下放这里行不行。在这里原则上还没有结束init呢

    def reset_all(self,time_delay=0.01):
        time.sleep(time_delay)
        self.text.setText("小弈人混-人机互动界面-客户端")
        self.dialog.setText("在此处输入人类作战意图，并点击按钮下达指令...")
        self.flag_order_renewed = False
    
    def get_status_str(self,status_str,step_num):
        if self.step_num == step_num and self.step_num>-114514 :
            # 异步通信的话态势这里要拿到步数还得改，就算了
            pass # 以防万一
        else:
            self.step_num = step_num
            self.text.setText(status_str)
            self.step_signal.emit(step_num)
    
    def get_human_order(self):
        return self.order_now

        
    @QtCore.Slot()
    def renew_order(self):
        self.text.setText("小弈人混-命令已经下达")
        self.order_now = self.dialog.text()
        self.flag_order_renewed = True
        # 这个得传过去
        self.socket_client.send_str(self.order_now)

        # # 这些是用来debug的
        # print(self.order_now)
        # time.sleep(3)
        # widget.get_status_str("小弈人混-人机互动界面测试114514",114)
        # self.get_status_str("小弈人混-人机互动界面测试114514",114)

    @QtCore.Slot(int)
    def update_all(self):
        pass
    
    @QtCore.Slot()
    def click_button(self):
        if self.p_status == "off":
            self.p_status = "on"
            self.socket_client.send_str("客户端命令：开始推演") # 写长一点，以防字符串匹配的时候有重复的
            self.button2.setText("停止")
        elif self.p_status == "on":
            self.p_status = "off"
            self.socket_client.send_str("客户端命令：停止推演")
            self.button2.setText("开始")
        else:
            raise Exception("p_status error")

if __name__ == "__main__":
    # 跑起来看看成色
    app = QtWidgets.QApplication([])

    widget = MyWidget()
    widget.resize(800, 300)
    widget.show()

    sys.exit(app.exec())