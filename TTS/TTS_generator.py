# 这个做个语音合成的，初定使用讯飞星火的在线的TTS
import hashlib
import requests
import pygame 
import threading
import _thread as thread
import base64
import hmac
import json
from datetime import datetime
from wsgiref.handlers import format_date_time
from time import mktime
from urllib.parse import urlencode
import websocket
import os
from pydub import AudioSegment
import ssl

class TTS_generator():

    def __init__(self) -> None:
      
        self.log_model_communication_name = r"TTS\log.txt"
        self.auto_test_location = r"D:\EnglishMulu\text_JSQL\auto_test"
        # self.auto_test_location = r"auto_test"
        self.ffmpeg_location = r"D:\ruanjian\ffmpeg-7.0.1-essentials_build\bin\ffmpeg.exe"
        self.pcm_name = r'\demo1.pcm'
        self.__init_AKSK()
        self.__init_net()
        pygame.init()
        pass

    def __init_AKSK(self):
        # print("model_communication: using qianfan")
        self.save_txt("TTS_generator: using xunfei")
        
        self.APPID = self.load_txt(r"TTS\APPID.txt")
        self.APIKey = self.load_txt(r"TTS\APIKey.txt")
        self.APISecret = self.load_txt(r"TTS\APISecret.txt")

        self.CommonArgs = {"app_id": self.APPID}
        self.BusinessArgs = {"aue": "raw", "auf": "audio/L16;rate=16000", "vcn": "xiaoyan", "tte": "utf8"}

        pass

    def __init_net(self):
        self.url = self.create_url()
        self.ws = websocket.WebSocketApp(self.url, on_message=self.on_message, on_error=self.on_error, on_close=self.on_close)

    def create_url(self):
        url = 'wss://tts-api.xfyun.cn/v2/tts'
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接字符串
        signature_origin = "host: " + "ws-api.xfyun.cn" + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + "/v2/tts " + "HTTP/1.1"
        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
            self.APIKey, "hmac-sha256", "host date request-line", signature_sha)
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        # 将请求的鉴权参数组合为字典
        v = {
            "authorization": authorization,
            "date": date,
            "host": "ws-api.xfyun.cn"
        }
        # 拼接鉴权参数，生成url
        url = url + '?' + urlencode(v)
        # print("date: ",date)
        # print("v: ",v)
        # 此处打印出建立连接时候的url,参考本demo的时候可取消上方打印的注释，比对相同参数时生成的url与自己代码生成的url是否一致
        # print('websocket url :', url)
        return url

    
    def on_message(self,ws,message):
        try:
            message =json.loads(message)
            code = message["code"]
            sid = message["sid"]
            audio = message["data"]["audio"]
            audio = base64.b64decode(audio)
            status = message["data"]["status"]
            # print(message)
            if status == 2:
                print("ws is closed")
                ws.close()
            if code != 0:
                errMsg = message["message"]
                print("sid:%s call error:%s code is:%s" % (sid, errMsg, code))
            else:

                with open(self.auto_test_location+self.pcm_name, 'ab') as f:
                    f.write(audio)
                # with open(self.auto_test_location+r'\demo.mp3', 'ab') as f:
                #     f.write(audio)

        except Exception as e:
            print("receive msg,but parse exception:", e)
                
    def text_to_voice(self,text:str):
        # 核心实现，调它的API，存出来
        self.Text = text
        self.Data = {"status": 2, "text": str(base64.b64encode(self.Text.encode('utf-8')), "UTF8")}

        # 然后开始通信了
        tongxin_thread = threading.Thread(target=self.run_single)
        tongxin_thread.start()

        # 返回一下这个线程，用来外面需要对齐的时候用。
        return tongxin_thread

    def set_pcm_name(self,pcm_name_str):
        self.pcm_name = "\\" +pcm_name_str
    
    def run_single(self):
        # pass
        self.ws.on_open = self.on_open
        self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        pass 

    def display_voice(self,location,name):
        # 简单的放一段，看看成色。
        # 这个东西按理说应该实现成一个异步的，让它自己跑着。来个线程池啥的？
        # 算了先别整list了，一个一个来好了。开一次这个函数就是播一段
        pcm_location = location + "\\" + name
        mp3_location = self.pcm_to_mp3(location,name[0:-4]) 
        display_thread = threading.Thread(target=self.display_voice_single,args=(mp3_location,))
        display_thread.start()

        return display_thread
    
    def pcm_to_mp3(self,location,name):
        pcm_location = location + "\\" + name + ".pcm"
        mp3_location = location + "\\" + name + ".mp3"
        sample_width = 2
        frame_rate = 16000
        channels = 1
        audio = AudioSegment.from_file(pcm_location, format="pcm", parameters=["-ar", "44100", "-f", "s16le"],sample_width=sample_width,frame_rate=frame_rate,channels=channels)
        audio.converter = self.ffmpeg_location # 暴力手改不可取，但是它既然是写死的，没考虑Windows下，那也就怪不得我了
        audio.export(mp3_location, format="mp3")
        return mp3_location

    def display_voice_single(self,location:str):
        # 单独的放一段，看看成色。
        pygame.mixer.music.load(location)
        pygame.mixer.music.play(1)
        # 等播放结束
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.music.stop()
        pass

    def load_txt(self,file_name):
        # 单纯的读取txt文件，主要是用来读那些key的。
        
        with open(file_name, 'r', encoding='utf-8') as f:
            neirong = f.read()
            return neirong
    def save_txt(self,neirong,file_name=""):
        # 单纯的写入txt文件，主要是用来记录对话的。
        if file_name == "":
            file_name = self.log_model_communication_name
        with open(file_name, 'a', encoding='utf-8') as f:
            f.write(neirong+"\n")
        return            

    # 收到websocket错误的处理
    def on_error(self,ws, error):
        print("### error:", error)


    # 收到websocket关闭的处理
    def on_close(self,ws, debug1, debug2):
        print("### closed ###")


    # 收到websocket连接建立的处理
    def on_open(self,ws):
        def run(*args):
            d = {"common": self.CommonArgs,
                "business": self.BusinessArgs,
                "data": self.Data,
                }
            d = json.dumps(d)
            print("------>开始发送文本数据")
            ws.send(d)
            if os.path.exists(self.auto_test_location+r'\demo.pcm'):
                os.remove(self.auto_test_location+r'\demo.pcm')

        thread.start_new_thread(run, ())

if __name__ == "__main__":
    TTS = TTS_generator()
    # TTS.text_to_voice("当朝大学士，统共有五位，朕不得不罢免四位")
    # TTS.text_to_voice("请注意，以上指令是基于当前态势的推演，实际情况可能需要根据战场变化做出调整。同时，由于敌方单位的接近，我方需要保持警惕，并准备应对敌方的反击。") # 运行会报错，但是报就报呗倒是也没有什么特别的所谓。生成的还挺快的。
    TTS.display_voice(TTS.auto_test_location, r'demo1.pcm')
    # TTS.display_voice_single(r'C:\\Users\\42418\\Desktop\\2024ldjs\\EnglishMulu\\text_JSQL\\auto_test\\demo1.mp3')