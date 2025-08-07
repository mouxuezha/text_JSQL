# 由于前端尚不具备状态，某学渣这里先实现一个画图的东西，怎么简单怎么来了。路数跟空天那个一样，用于降低抽象程度。
from matplotlib.colors import Colormap
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Line3DCollection
from matplotlib import rcParams
import matplotlib as mpl
import os.path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
from numpy import cos,sin
import os 
import pickle
import time

class huatu():
    def __init__(self,**kargs):
        self.x_name = 'x'
        self.y_name = 'y'
        self.title = 'huatu'
        self.yanse = ['C0','C1','C2','C3','C4','C5','C6']
        self.status_list = [] 
        self.save_location = "auto_test/huatu"
        self.fig = None 
        self.ax = None

    def init_plot3d(self):
        # 吸取以前的教训，还是好好传值传引用，别搞得全局变量满天飞，不太好。
        plt.style.use("_mpl-gallery")
        fig,ax = plt.subplots(subplot_kw={"projection":"3d"})
        bili = 1
        fig.set_figheight(4.3267717*bili)
        fig.set_figwidth(5.9251969*bili) # 5.9251969 inches = 15.05cm which is used in MS word
        self.fig = fig 
        self.ax = ax
        return fig,ax
    
    def init_plot2d(self):
        # 这个的说法是用来画二维的曲线图，
        # 吸取以前的教训，还是好好传值传引用，别搞得全局变量满天飞，不太好。
        fig, ax = plt.subplots()
        bili = 1
        fig.set_figheight(4.3267717*bili)
        fig.set_figwidth(5.9251969*bili) # 5.9251969 inches = 15.05cm which is used in MS word
        self.fig = fig 
        self.ax = ax
        return fig, ax
    
    def show_plot(self):
        self.ax.set_aspect("equal")
        plt.show() # 这东西是阻塞的，比较尴尬，用的时候慎用。
        print("finish drawing something") 
    
    def save_fig(self,name="huatu"):
        wenjianming_tu = self.save_location  + '/' + name + '.png'
        plt.savefig(wenjianming_tu,dpi=1200)
        # plt.show()
        plt.close()    

    def visual_status_2D(self,timestep,red_status,blue_status):
        # 这个是随着时间画出点列的，要输入红蓝态势。
        # 完整来一次，取数画图存储。
        fig,ax = self.init_plot2d()

        red_x,red_y,red_ID = self.get_points(red_status)
        blue_x,blue_y,blue_ID = self.get_points(blue_status)

        # 然后开始画图并标注
        ax = self.draw_points(ax,red_x,red_y,red_ID,side="red")
        ax = self.draw_points(ax,blue_x,blue_y,blue_ID,side="blue")

        ax = self.set_ticks_LLA(ax)
        # self.show_plot()
        self.save_fig(name="visual_2d" + str(timestep))

    def get_points(self,status):
        # 对一组态势里面的所有单位，把那些个东西取出来。
        x = [] 
        y = [] 
        ID_list = [] 
        for attacker_ID in status:
            x_single = status[attacker_ID]["VehicleState"]["lon"]
            y_single = status[attacker_ID]["VehicleState"]["lat"]
            ID_single = attacker_ID
            x.append(x_single)
            y.append(y_single)
            ID_list.append(ID_single)
        
        return x,y,ID_list
    
    def draw_points(self,ax,red_x,red_y,red_ID,side="red"):

        ax.scatter(red_x,red_y,s=10,color=side)
        
        for i in range(len(red_ID)):
            # 来来来，开始狠狠地标注。
            ax.text(red_x[i],red_y[i],red_ID[i],fontsize=8,ha="center",va="center",color=side)

        return ax

    def set_ticks_LLA(self,ax):
        # 这个是直接画图，可惜没有什么好的办法把海岸线画出来。
        ax.set_xlim(47.00-2, 49.00+1) # 经度 
        ax.set_ylim(12.00-2, 14.00+1) # 纬度
        plt.tick_params(axis="both",which="major",labelsize = 12 , direction="in", length=8)  
        self.ax.set_aspect("equal") # 由于都是2度，所以也可以equal。
        return ax   
