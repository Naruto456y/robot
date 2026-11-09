import os,sys,time,threading,requests

from xinghou_speak_iat import rec_wav_music
from tonyi_video_api import *
from recode_video import *
from xinghou_tts import *

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from API_KEY import *
from audio import start_recording, detect_keyword
from tongyi_speak_iat import rec_wav_music_Tongyi #阿里的音频识别
from tongyi_tts import tonyi_tts #阿里的音频合成

response = ''
def Speak_Vioce():
    global response
    if TTS_IAT_Tongyi:
        tonyi_tts(response)
    else:
        Xinghou_speaktts(response)#播放音频 PLAY AUDIO



#Test the network
net = False
try:
    html = requests.get("http://www.baidu.com", timeout=2)
    net = True
except Exception as e:
    print(f"Network check failed: {e}")
    net = False

#Record and control the dog
if net:
    while True:
        if detect_keyword():
            os.system("pkill mplayer") 
            time.sleep(.2)
            
            start_recording()
            time.sleep(1)
            
            
            if TTS_IAT_Tongyi:
                content = rec_wav_music_Tongyi()
            else:
                content = rec_wav_music()
                
            #content ='红色小球有没有被人拿走'
            if content != "":
                print("Q:"+content)
                
                record_video()#录制视频
                
                re =Tongyi_video_api(content)

                print("A:"+re)
                try:
                    response = re
                    tts_thread = threading.Thread(target=Speak_Vioce)
                    tts_thread.daemon = True  
                    tts_thread.start()
                    
                except:
                    pass
                
                play_video()#播放录制视频
            if content == 0:
               break
        time.sleep(0.1)  
else:
    print("检测网络没连上，请重启")
    while True:
        time.sleep(0.1)

