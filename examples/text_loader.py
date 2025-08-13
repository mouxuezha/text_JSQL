# 这个的设想是做成一个统一的读取JSON的，然后从外面再来取那些文字。
# 一定要十分注意结构化和工程化，这样才能
import json
import os.path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class text_loader():
    def __init__(self):
        self.data_location = "examples"
        self.case_name = "对海打击红方.json"
        self.data = {}
        self.load_JSON()
        pass

    def load_JSON(self):
        file_location = self.data_location + "/" + self.case_name
        with open(file_location, "r", encoding="utf-8") as f:
            self.data=json.load(f)
        pass 

    def set_case(self,case_name="对海打击红方.json"):
        self.case_name = case_name
        pass

    def get_certain_text(self, function_name, text_name):
        jieguo = self.data[function_name][text_name]
        return jieguo
    
    def check_state_candidate_2024(self,state_candidate_single):
        # 先check掉一些不对的。# 这个是根据场景特征定制的，主要是通过这个check，来进行降维，不然维度太多就玩不了了。
        # 难顶的是，这部分还不好弄到JSON里面去。只好整个函数挪过去了。
        flag_check = True
        state_enmueration_dict = self.get_certain_text("text_transfer.__init_DeLLMa","state_enmueration_dict")
        if state_candidate_single["敌方经度"] != state_enmueration_dict["敌方经度"][1]:
            flag_check = False
        if not("北" in state_candidate_single["敌方纬度"]):
            flag_check = False
        if not("南" in state_candidate_single["我方纬度"]):
            flag_check = False
        if state_candidate_single["我方聚集程度"] != state_enmueration_dict["我方聚集程度"][2]:
            flag_check = False
        if state_candidate_single["敌方聚集程度"] != state_enmueration_dict["敌方聚集程度"][1]:
            flag_check = False
        return flag_check
    
    def check_state_candidate_2025_red(self,state_candidate_single ):
        flag_check = True
        state_enmueration_dict = self.get_certain_text("text_transfer.__init_DeLLMa","state_enmueration_dict")
        if state_candidate_single["敌方航母经度"] != state_enmueration_dict["敌方航母经度"][0]:
            flag_check = False
        if state_candidate_single["敌方航母纬度"] ==  state_enmueration_dict["敌方航母纬度"][0]:
            flag_check = False
        if state_candidate_single["我方弹药余量"] ==  state_enmueration_dict["我方弹药余量"][0]:
            flag_check = False
        if state_candidate_single["敌方阵形"] !=  state_enmueration_dict["敌方阵形"][0]:
            flag_check = False
        if state_candidate_single["我方侦察进度"] ==  state_enmueration_dict["我方侦察进度"][0]:
            flag_check = False            
        return flag_check 
    
    def check_state_candidate_2025_blue(self,state_candidate_single ):
        flag_check = True
        state_enmueration_dict = self.get_certain_text("text_transfer.__init_DeLLMa","state_enmueration_dict")
        raise Exception("unfinished yet")
        return flag_check 
    
    