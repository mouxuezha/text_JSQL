# 这个是整理一下之前的，实现单台电脑上的、使用雪楠哥他们前端的，人机交互

from dialog_box.dialog_box_server import MyWidget as MyWidget_server
from dialog_box.dialog_box_client2 import MyWidget as MyWidget_client
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtWidgets import QDialog 

import threading,time 

class auto_run_comunicator():
    # 本来是早都该弄的了，自动化的启动器。那现在弄一下好了。
    def __init__(self):
        # 初始化一系列的通信啥的东西。
        self.config = {"red_ip":"127.0.0.1", "red_port": "31001",
                    "blue_ip": "127.0.0.1", "blue_port": "31002","flag_server_waiting":True,"dialog_box_model": "QtC++","socket_debug_model":"net_debug"}
        
        # 不能直接这么来，直接这么来就阻塞了。
        # self.__init_server()
        # self.__init_client_red()
        # self.__init_client_blue()

        # 原则上初始化完了就可以看着了，只要保证主线程不退出。
    
    def __init_server(self):
        print("init dialog_box_server")
        app = QtWidgets.QApplication([])
        config = self.config
        self.widget_server = MyWidget_server(config=config)
        self.widget_server.resize(800, 300)
        self.widget_server.show()        
        pass 

    def __init_client_red(self):
        time.sleep(1.14514)
        print("init dialog_box_client2 for red player")
        
        config = self.config    # dialog_box_model能选QtC++和QtPython，socket_debug_model有local_debug和net_debug，区别是用不用那个假的socket类。
        # 这个config其实是服务于command_processor的，不是服务于dialogbox，所以原则上其他的dialogbox也可以用。
        config["UI_port"] = 30002
        self.widget_red = MyWidget_client(role="red_player",config = config)
        self.widget_red.run_mul()        
        pass 
    
    def __init_client_blue(self):
        time.sleep(1.14514*2)
        print("init dialog_box_client2 for blue player")
        
        config = self.config    # dialog_box_model能选QtC++和QtPython，socket_debug_model有local_debug和net_debug，区别是用不用那个假的socket类。
        # 这个config其实是服务于command_processor的，不是服务于dialogbox，所以原则上其他的dialogbox也可以用。
        config["UI_port"] = 30003
        self.widget_blue = MyWidget_client(role="blue_player",config = config)

        self.widget_blue.run_mul()        
        pass 

    def run_mul(self):
        # 还得开多线程。不然建立连接那一步是阻塞的，直接就尬住了。
        thread1 = threading.Thread(target=self.__init_server)
        thread2 = threading.Thread(target=self.__init_client_red)  
        thread3 = threading.Thread(target=self.__init_client_blue)          
        
        # 然后就启动线程呗
        thread1.start()
        thread2.start()
        thread3.start()

        # 这个就是开一个主线程等着而已。既然如此那做一个命令行退出的东西可也。
        while(True):
            user_input = input("输入exit退出程序。")
            if user_input == "exit":
                break
            else:
                # 实际效果是输入错了就重新输。也留出后续扩展其他命令行功能的接口。
                pass

        pass

if __name__ == "__main__":
    shishi = auto_run_comunicator()
    shishi.run_mul()