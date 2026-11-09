import os,sys,time,threading,requests


from creat_img_tongyi import *

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from audio import start_recording, detect_keyword

from xinghou_speak_iat import rec_wav_music
from tongyi_speak_iat import rec_wav_music_Tongyi




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
            
            start_recording()
            
            if TTS_IAT_Tongyi:
                content = rec_wav_music_Tongyi()
            else:
                content = rec_wav_music()

            if content != "":
                
                print("Q:"+content)                
                tongyi_image_creat(content)
                
            if content == 0:
               break

        time.sleep(0.1)  
else:
    print("请检查网络连接,重启")
    while True:
        time.sleep(0.1)

