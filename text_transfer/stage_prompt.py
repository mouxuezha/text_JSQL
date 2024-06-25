# 这个试图实现一个“根据当前的帧数判断是什么阶段”的东西，从而做一个“到一定步数就命令全员A到点里去”这样的。
# TODO: 再做一个输入态势之后计算敌我啥的，然后生成一堆文字来描述态势的功能。


class StagePrompt:
    def __init__(self, flag_kaiguan=True):
        self.stage_now = "机动"
        # 先初步划分一下，“机动”阶段（前期，调一下阵型，上下车啥的，如有），“交战”阶段（不加什么特效），“夺控”阶段。
        self.flag_kaiguan = flag_kaiguan
        pass

    def get_stage_now(self, time_step):
        # 根据当前帧数判断是什么阶段，突出一个怎么快怎么来。
        if time_step < 400:
            self.stage_now = "机动"
        elif time_step <700:
            self.stage_now = "侦察"
        elif time_step < 1500:
            self.stage_now = "交战"
        elif time_step < 2999:
            self.stage_now = "夺控"
        else:
            self.stage_now = "机动"
        return self.stage_now
        pass

    def get_stage_prompt(self, time_step):
        # 先确定一下当前的阶段，然后根据阶段生成一些prompt
        if self.flag_kaiguan == False:
            # 关闭状态，直接返回个空的。
            return ""
        self.get_stage_now(time_step)
        prompt = "当前时间步长为" + str(time_step) + "，"
        
        # 这个是人混的时候加的。
        prompt = "如无具体命令，则" + prompt
        
        if self.stage_now == "机动":
            prompt = prompt+ "请命令各单位优先向夺控点方向搜索前进，步兵不下车，无人机探测夺控点附近"
        elif self.stage_now == "交战":
            prompt = prompt+  "请命令各单位占据有利地形、形成有利阵型，有效打击敌人。"
        elif self.stage_now == "夺控":
            prompt = prompt+  "请命令各单位迅速向夺控点前进，并清缴夺控点周围敌人。"
        elif self.stage_now == "侦察":
            prompt = prompt+  "请命令坦克停止前进，步兵下车，并命令无人机移动到东南方向移动以探查敌情"
        return prompt
        