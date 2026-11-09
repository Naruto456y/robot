import os,sys,base64
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from API_KEY import *
from openai import OpenAI



def get_response(messages): #执行层智能体模型
    MODEL='qwen-vl-max-2025-04-08'
    client = OpenAI(
        api_key=TONYI_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    completion = client.chat.completions.create(model=MODEL, messages=messages)
    return completion

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

messages = [
        {
            "role": "system",
            "content": """你是一个麦轮小车助手，如果有听到再见、退出的意思，你要说：好的再见，有需要再找我喔。""",
        }
    ]

assistant_output = "xxx"

def New_session_init():
    global messages,assistant_output
    # 初始化一个 messages 数组
    messages = [
        {
            "role": "system",
            "content": """你是一个麦轮小车助手，如果有听到再见、退出的意思，你要说：好的再见，有需要再找我喔。""",
        }
    ]

    assistant_output = "xxx"



def QwenVL_api_picture(PROMPT='执行智能体'):
    global messages,assistant_output,new_speak
    base64_image = encode_image("./AI_CarAgent/rec.jpg") #AI_CarAgent/
    
    if "有需要再找我喔" not in assistant_output:
        # 将用户问题信息添加到messages列表中
        messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpg;base64,{base64_image}"}, 
                    },
                    {"type": "text", 
                     "text": PROMPT
                    },
                ],
            })
        assistant_output = get_response(messages).choices[0].message.content
        
        # 将大模型的回复信息添加到messages列表中
        messages.append({"role": "assistant", "content": assistant_output})
        #print(f"模型输出：{assistant_output}")
        #print("\n")
        
        if "有需要再找我喔" in assistant_output: #输出结果会在下一个问题前更新
            #print("清空对话")
            exit = assistant_output  
            New_session_init()  
            return exit
        
        return assistant_output
      
      

       
def QwenVL_api_decision(PROMPT='决策智能体'):
    client = OpenAI(
        api_key=TONYI_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    completion = client.chat.completions.create(
        # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
        model="qwen-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": PROMPT},
        ],
    )
    #print(completion.model_dump_json())
    result = completion.choices[0].message.content
    #print(result)
    return result