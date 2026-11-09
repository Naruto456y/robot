from Car_base_control import *
from openai import OpenAI
import os,sys,time,threading,cv2,base64
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from API_KEY import *
from Car_Online_API import Api_picture_en

def is_mplayer_playing():
    try:
        result = subprocess.check_output(['pgrep', '-l', 'mplayer'])
        if not result:
            return False
        return True
    except subprocess.CalledProcessError:
        return False


def Image_Describe_Fun(str="Describe what you saw"):
    
    take_photo_agent()
    
    img = cv2.imread("./AI_CarAgent_en/rec.jpg")
    cv2.imshow('image',img)
    cv2.waitKey(1)
    
    response = Api_picture_en(str+'Please limit the answer to 30 words and add \'I saw it\' at the beginning of the answer')
    print(response)
    
    Xinghou_speaktts(response)#播放音频 PLAY AUDIO
    
    while is_mplayer_playing():#等待播放完成
        pass
    cv2.destroyAllWindows()
    
    
mystr = sys.argv[1]  
Image_Describe_Fun(mystr)