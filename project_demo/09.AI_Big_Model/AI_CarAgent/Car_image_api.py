from Car_base_control import *
from openai import OpenAI
import os,sys,time,threading,cv2,base64
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from API_KEY import *
from Car_Online_API import QwenVL_api_picture

def is_mplayer_playing():
    # 检查mplayer进程是否存在
    try:
        # 使用pgrep查找mplayer进程
        result = subprocess.check_output(['pgrep', '-l', 'mplayer'])
        if not result:
            return False
        return True
    except subprocess.CalledProcessError:
        return False

# def encode_image_ooo(image_path):
#     with open(image_path, "rb") as image_file:
#         return base64.b64encode(image_file.read()).decode("utf-8")


# def tongyi_Image_litle(imagetext):
#     base64_image = encode_image_ooo("./AI_CarAgent/rec.jpg")
#     client = OpenAI(
#         api_key=TONYI_key,
#         base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
#     )
#     completion = client.chat.completions.create(
#         model="qwen-vl-plus",  # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
#         messages=[{"role": "user","content": [
#                 {"type": "image_url",
#                 "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
#                 {"type": "text", "text": imagetext},
#                 ]}]
#         )
#     #print(completion.model_dump_json())
#     result = completion.choices[0].message.content
#     # print(result)

#     return result


def Image_Describe_Fun(str="描述下你看到了什么"):
    
    take_photo_agent()
    cv2.destroyAllWindows()
    
    img = cv2.imread("./AI_CarAgent/rec.jpg")
    cv2.imshow('image',img)
    cv2.waitKey(1)
    
    #response = tongyi_Image_litle(str+'请限制在30个字内，并且回答开头要加上"我看到了"')
    response = QwenVL_api_picture(str+'请限制在30个字内，并且回答开头要加上"我看到了"')
    
    print(response)
    
    if TTS_IAT_Tongyi:
        tonyi_tts(response)
    else:
        Car_Xinghou_speaktts(response)#播放音频 PLAY AUDIO
    
    while is_mplayer_playing():#等待播放完成
        pass
    #print("image exit")
    cv2.destroyAllWindows()
    del img


mystr = sys.argv[1]  
Image_Describe_Fun(mystr)