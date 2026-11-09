import os,base64
from http import HTTPStatus
from dashscope import Application

import os,sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from API_KEY import *



assistant_output = ''
Amessages = []

def New_session_agnet():
    global Amessages,assistant_output
    Amessages = []
    assistant_output = ''


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



def analyze_image(image_path,inputstr):
    
    global assistant_output,Amessages
    image_data = image_to_base64(image_path)
    
    
    if "有需要再找我喔" not in assistant_output:
        Amessages.append(
        {
            "role": "user","content": inputstr
        })
        
        #print(Amessages)
        
        response = Application.call(
            api_key=TONYI_key,
            app_id=Online_Iamge_ID,  # 替换为实际的应用 ID
            messages=Amessages,
            image_list=[image_data] # 使用Base64格式的本地图片
            ) 
        
        
        if response.status_code != HTTPStatus.OK:
            print(f"请求失败(request_id={response.request_id})")
            print(f"错误代码: {response.status_code}")
            print(f"错误信息: {response.message}")
            print("参考文档: https://help.aliyun.com/zh/model-studio/developer-reference/error-code")
            New_session_agnet()  #清除数据
        else:           
            assistant_output = response.output.text
            if "有需要再找我喔" in assistant_output: #输出结果会在下一个问题前更新
                #print("清空对话")
                New_session_agnet() 
                return response
                
            Amessages.append({"role": "assistant", "content": assistant_output})
            return response
            

def Car_Tongyi_Image_Agent(PROMPT = '在线封装的智能体'):
    IMAGE_PATH = "./AI_CarAgent/rec.jpg"  # 本地图片路径  
    
    try:
        response = analyze_image(IMAGE_PATH, PROMPT)
        
        if response.status_code != HTTPStatus.OK:
            print("Angent Fail!")
        else:           
            return response.output.text
        
    except FileNotFoundError as e:
        print(f"错误: {str(e)}")
        
    except Exception as e:
        print(f"智能体信息发生错误: {str(e)}")
    


# if __name__ == '__main__':
#     while 1:
#         inputstr = input("请输入:")
#         bbb = Car_Tongyi_Image_Agent(inputstr)
#         print(bbb)