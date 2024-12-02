# 这个是服务器端的，用于原位替代本地版本的dialog_box
# 原则上，复制粘贴代码是比较傻逼的行为，但是我菜，嘿嘿嘿

import os.path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from socket_communication.socket_server import socket_server_2player
from main import command_processor
import random
import time 
import threading

from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtWidgets import QDialog 

class MyWidget(QtWidgets.QWidget):
    # 这边事实上不需要界面，只需要在收到传过来的消息的时候触发相应的信号，从而触发相应的槽函数即可。
    # 讲道理，完全可以做成“服务器端点也行，在这点也行”的模式嘛。
    
    step_signal = QtCore.Signal(int) # 这个用来刷新的，下一步把窗口里的所有东西都刷新一遍。
    def __init__(self,**kargs):
        super().__init__()
        self.order_now = "none"
        self.flag_order_renewed = False
        
        # 人跟人打，就要有特定的说法了。干脆重新规划一下，红蓝方都以客户端的形式给出，哪怕是本地的也行。然后这个server彻底作为一个中间层存在，不再显示界面了
        self.order_now_client = "none"
        self.flag_order_renewed_client = False        
        self.status_to_send = "态势："

        self.step_num = 0
        # self.p_status ="on" # 为了后面能走，这个得默认是on
        self.p_status ="off" # 由于server里面加了新逻辑，这个得是off了
        config = kargs["config"]
        self.p = command_processor(self,role="server",config=config)

        # IP是服务器这台电脑在内网的IP，端口用个不一样的。
        self.socket_server = socket_server_2player(config,dialog_box=self,model="debug")
        
        
        self.button = QtWidgets.QPushButton("下达命令")
        self.button2 = QtWidgets.QPushButton("开始")
        self.text = QtWidgets.QLabel("小弈人混-人机互动界面-服务器",
                                     alignment=QtCore.Qt.AlignCenter)

        self.dialog =  QtWidgets.QLineEdit("在此处输入人类作战意图，并点击按钮下达指令...")
        self.reset_all()  
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.text)
        self.layout.addWidget(self.dialog)
        self.layout.addWidget(self.button)
        self.layout.addWidget(self.button2)

        # 然后是定义信号和槽相关的内容，没几个所以不另开函数了
        self.button.clicked.connect(self.renew_order)
        self.step_signal[int].connect(self.update_all) 
        self.button2.clicked.connect(self.click_button)

        self.socket_server.run_mul() # 试一下放这里行不行。在这里原则上还没有结束init呢

        # 新的逻辑：为了实现服务器端的监听，直接开局的时候就触发一下
        # 偷懒了，开局直接按按钮，照道理说是没问题的。
        # self.click_button()  # 这个是用Qthread去开
        self.run_mul() # 这个是用原来的threading去开，不要信号槽的
    
    def run_mul(self):
        # 换个方式开多线程。那个Qthread那个调试不了就很伤，搞得很傻逼。
        self.thread1 = threading.Thread(target=self.run_single)

        self.thread1.start()

        print("main_loop_wrap start in threading")
    
    def run_single(self):
        # 这个就是为了分线程而设置的
        self.p.main_loop_wrap()

    def reset_all(self,time_delay=0.01):
        time.sleep(time_delay)
        self.text.setText("小弈人混-人机互动界面")
        self.dialog.setText("在此处输入人类作战意图，并点击按钮下达指令...")
        self.flag_order_renewed = False
    
    def get_status_str(self,status_str,step_num):
        if (self.step_num == step_num and self.step_num>100) and False :
            # 后面那个and是用来方便开关的。
            pass # 以防万一
        else:
            self.step_num = step_num
            self.text.setText(status_str)
            # 这个get_status_str是在main里面调的，调到就说明态势更新了，所以传就完事儿了
            self.socket_server.send_to_players(status_str)
            self.step_signal.emit(step_num)
    
    def get_human_order(self):
        return self.order_now

        
    @QtCore.Slot()
    def renew_order(self):
        self.text.setText("小弈人混-命令已经下达")
        self.order_now = self.dialog.text()
        self.flag_order_renewed = True
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
            self.p.start()
            self.button2.setText("停止")
        elif self.p_status == "on":
            self.p_status = "off"
            self.p.terminate()
            self.button2.setText("开始")
        else:
            raise Exception("p_status error")                
        

if __name__ == "__main__":
    # 跑起来看看成色
    app = QtWidgets.QApplication([])
    config = {"red_ip":"192.168.1.140", "red_port": "20001",
                "blue_ip": "192.168.1.140", "blue_port": "20002","flag_server_waiting":True }
    widget = MyWidget(config=config)
    widget.resize(800, 300)
    widget.show()

    sys.exit(app.exec())    