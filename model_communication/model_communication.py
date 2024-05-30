# 这个先以mouxuezha比较熟悉的百度文心千帆来实现。

import requests
import qianfan

class model_communication():
    def __init__(self):
        self.qianfan_api_key = 'YOUR_QIANFAN_API_KEY'
        self.qianfan_api_url = 'https://api.qianfan.com/v1/chat'
        self.baidu_api_key = 'YOUR_BAIDU_API_KEY'
        self.baidu_api_url = 'https://aip.baidubce.com/rpc/2.0/unit/service/chat'
    
    def communicate_with_model(self, message):
        # 调用百度文心千帆模型
        pass

if __name__ == '__main__':
    communication = model_communication()
    communication.communicate_with_model('你好')