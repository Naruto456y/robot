from openai import OpenAI
import os,sys
import base64

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from API_KEY import *

#  Base64 编码格式
def encode_video(video_path):
    with open(video_path, "rb") as video_file:
        return base64.b64encode(video_file.read()).decode("utf-8")

def Tongyi_video_api(strQA="视频描绘的是什么景象?"):
    base64_video = encode_video("./VideoDescription/record_video.mp4")
    client = OpenAI(
        api_key=TONYI_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    completion = client.chat.completions.create(
        model="qwen-vl-plus-latest",  
        messages=[
            {
                "role": "system",
                "content": [{"type":"text","text": "You are a helpful assistant."}]},
            {
                "role": "user",
                "content": [
                    {
                        
                        "type": "video_url",
                        "video_url": {"url": f"data:video/mp4;base64,{base64_video}"},
                    },
                    {"type": "text", "text": strQA},
                ],
            }
        ],
    )
    #print(completion.choices[0].message.content)
    return completion.choices[0].message.content