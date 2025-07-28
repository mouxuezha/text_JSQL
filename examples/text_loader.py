# 这个的设想是做成一个统一的读取JSON的，然后从外面再来取那些文字。
# 一定要十分注意结构化和工程化，这样才能
import json
import os.path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class text_loader():
    def __init__(self):
        self.data_location = "examples"
        self.case_name = "陆火联合.json"
        self.data = {}
        self.load_JSON()
        pass

    def load_JSON(self):
        file_location = self.data_location + "/" + self.case_name
        with open(file_location, "r", encoding="utf-8") as f:
            self.data=json.load(f)
        pass 

    def set_case(self,case_name="陆火联合.json"):
        self.case_name = case_name
        pass

    def get_certain_text(self, function_name, text_name):
        jieguo = self.data[function_name][text_name]
        return jieguo
    
