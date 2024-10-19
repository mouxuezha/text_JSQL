# 这个是用来研究一下屏幕截图的，准备拿去搞多模态大模型的

import os.path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import win32gui
import win32con
import PIL
from PySide6.QtWidgets import QApplication 

import pygetwindow as gw 
import pyautogui

import time 
import threading

class image_manager():
    # 也是开个多线程跑着，然后非阻塞地截图，存在特定的文件夹里面备用。
    def __init__(self):
        self.folder = "auto_test\\images"
        self.hwnd_title = dict()
        self.index  = 0 
        self.flag_signal = False # 变成用很笨的办法实现了一个信号槽机制了。好在问题简单，笨就笨点，就不依赖Qt了。
        pass

    def run_mul(self):
        # 已经形成习惯了，跟别的一样，只要把这个启动起来别的就不用管了。
        self.thread1 = threading.Thread(target=self.run_single)
        
        self.thread1.start()

        print("image_manager ready")


    def run_single(self):
        # 得琢磨，是周期性截图存着，还是被触发了截图需要的时候才截图。
        # 目前认为是有需要的时候再截图是比较好的。
        while True:
            # 既然是阻塞的进程，那就得来点儿sleep。
            time.sleep(0.5)
            if self.flag_signal ==False:
                # 那就是说，没有人提过截图的需求。
                pass
            elif self.flag_signal ==True:
                # 那就是说，有人通过get_one_picture函数提出过“截个图”的需求了，那就截个图。
                window = self.get_window()
                self.get_screen_shoot(window)
                self.flag_signal = False
                print("finsh one screen_shoot")

    def get_one_picture(self):
        # 改标志位，返回路径。
        self.flag_signal = True
        name = self.folder + '\\jietu' + str(self.index) + ".png"
        return name
    
    def get_all_hwnd(self):
        # 这个技术路径最终并未选用。
        hwnd = win32gui.FindWindow(None,"白方显示")
        app = QApplication(sys.argv)
        screen = QApplication.primaryScreen()
        # win32gui.SetForegroundWindow(hwnd) # 试图把窗口切出来，但是并没有什么用，不成功。
        win32gui.ShowWindow(hwnd,win32con.SW_SHOWMAXIMIZED)
        img = screen.grabWindow(hwnd).toImage()
        img.save(self.folder + '\\shishi.jpg')
    
    def get_window(self):
        windows = gw.getAllTitles()
        target_window_title = "白方显示"
        # target_window_title = "任务管理器"
        
        window = None # 考虑点容错
        if target_window_title in windows:
            # 那就是有界面
            target_window = gw.getWindowsWithTitle(target_window_title)
            if target_window:
                # 说明是找到了
                window = target_window[0]
            else:
                print("get_screen_shoot can not find window")        
        else:
            # 那就是没有界面
            print("get_screen_shoot can not find window")      

        return window
    
    def get_screen_shoot(self, window:gw._pygetwindow_win.Win32Window):
        # 摆烂了，先把窗口切出来然后截图。
        try:
            window.activate()
        except:
            window.minimize()
            window.maximize()
        
        time.sleep(0.05) # 这里要稍微来一点点延时，不然程序跑到后面截图的时候窗口还没切出来就尴尬了。

        # 先把窗口边界拿出来。
        # left = window.left
        # top = window.top
        # width = window.width
        # height = window.height
        left = -8 # 硬编码的全屏，以防有时候读取到的窗口位置不对
        top = -8
        width = 1936
        height = 1056
        # 然后截图了。
        screen_shot = pyautogui.screenshot(region=(left,top,width,height))

        name = self.folder + '\\jietu' + str(self.index) + ".png"
        screen_shot.save(name)
        self.index = self.index + 1
        # window.minimize() # 完事再切回去，神不知鬼不觉
        pass 

    def __del__(self):
        self.thread1.join()

if __name__ == "__main__":
    shishi_image_manager = image_manager()
    flag = 1
    if flag == 0:
        # shishi_image_manager.get_all_hwnd()
        window = shishi_image_manager.get_window()
        shishi_image_manager.get_screen_shoot(window)
    elif flag == 1:
        # 进一步的测试：开起多线程来，然后如果能够以正常的时间间隔触发，并且截图出来，那就说明是没问题的，不然就是有问题的了。
        shishi_image_manager.run_mul()
        for i in range(10):
            time.sleep(5)
            print("现在是第"+str(i)+"个了，准备开始截图")
            name = shishi_image_manager.get_one_picture()
            print(name)



    