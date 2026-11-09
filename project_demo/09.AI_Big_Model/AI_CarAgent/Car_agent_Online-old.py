import os,base64
from http import HTTPStatus
from dashscope import Application

import os,sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from API_KEY import *





def image_to_base64(image_path):
    """将本地图片转换为Base64编码字符串"""
    with open(image_path, 'rb') as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    
    # 根据文件类型自动判断MIME类型
    ext = os.path.splitext(image_path)[1].lower()
    mime_type = {
        '.jpg': 'jpeg',
        '.jpeg': 'jpeg',
        '.png': 'png',
        '.gif': 'gif',
        '.bmp': 'bmp',
        '.webp': 'webp'
    }.get(ext, 'jpeg')  # 默认使用jpeg
    
    return f"data:image/{mime_type};base64,{encoded_string}"

def analyze_image(image_path, prompt):
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"图片不存在: {image_path}")
    
    
    image_data = image_to_base64(image_path)
    
    # 调用视觉智能体API
    response = Application.call(
        api_key=TONYI_key,
        app_id=Online_Iamge_ID,
        prompt=prompt,
        image_list=[image_data]  # 使用Base64格式的本地图片
    )
    
    return response

    
#在线智能体接口    
def Car_Tongyi_Image_Agent(PROMPT = '在线封装的智能体'): 
    IMAGE_PATH = "./AI_CarAgent/rec.jpg"  # 本地图片路径
    try:
        response = analyze_image(IMAGE_PATH, PROMPT)
        
        if response.status_code != HTTPStatus.OK:
            print(f"请求失败(request_id={response.request_id})")
            print(f"错误代码: {response.status_code}")
            print(f"错误信息: {response.message}")
            print("参考文档: https://help.aliyun.com/zh/model-studio/developer-reference/error-code")
        else:           
            # agent_plan_execute = eval(response.output.text)
            # print(agent_plan_execute['response'])
            #print(response.output.text)
            return response.output.text
        
    except FileNotFoundError as e:
        print(f"错误: {str(e)}")
        
    except Exception as e:
        print(f"智能体信息发生错误: {str(e)}")
        

