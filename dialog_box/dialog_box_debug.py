# 这个是用来debug的，配合main函数

class MyWidget_debug:
    def __init__(self,role="server",**kargs):
        # 这个是用来隔离一下，单独debug一下main_loop的
        self.timestep = 0
        self.flag_order_renewed = False
        self.order_now = "test"

    def get_status_str(self,status_str, timestep):
        # 获取当前状态
        pass
    def get_human_order(self):
        return self.order_now
    
    def reset_all(self, canshu=0):
        # 重置所有状态
        pass

class MyWidget_debug2:
    # 这个是用来模拟有人类干预的情形的，以进行测试。就是先模拟发一些人类指令，根据不同的步数，然后看看情况。
    def __init__(self):
        # 这个是用来隔离一下，单独debug一下main_loop的
        self.timestep = 0
        self.flag_order_renewed = False
        self.order_now = ""
    
    def get_status_str(self,status_str, timestep):
        # 这个是总开关 # 但是其实不必要，用MyWidget_debug而不是MyWidget_debug2，就是把拟似人类命令都关了的
        # return 

        # 获取当前状态
        if timestep == 300:
            self.order_now = "请命令无人机向地图区域东南方向移动以敌情。"
            self.flag_order_renewed = True
        elif timestep ==  210:
            self.order_now = "请命令步兵战车放下步兵，并向夺控点附近搜索前进"
            self.flag_order_renewed = True
        elif timestep == 2000:
            self.order_now = "请命令我方单位进行适当的移动以分散部署位置，以防遭到打击。"
            self.flag_order_renewed = True
        
        
        pass

    def get_human_order(self):
        return self.order_now
    
    def reset_all(self, canshu=0):
        # 重置所有状态
        self.flag_order_renewed = False
        self.order_now = ""
        pass       