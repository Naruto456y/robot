from openai import OpenAI
import os,sys,time,threading,requests

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from API_KEY import *


messages = [
        {
            "role": "system",
            "content": """你是一个知识百科助手，如果有听到再见、退出的意思，你要说：好的再见，有需要再找我喔。""",
        }
    ]

assistant_output = "我是一个你的生活常识小助手，请问有什么能帮助你呢?"

def get_response(messages):
    client = OpenAI(
        api_key=TONYI_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    completion = client.chat.completions.create(model="qwen-plus", messages=messages)
    return completion

def New_session_init():
    global messages,assistant_output
    # 初始化一个 messages 数组
    messages = [
        {
            "role": "system",
            "content": """你是一个知识百科助手，如果有听到再见、退出的意思，你要说：好的再见，有需要再找我喔。""",
        }
    ]

    assistant_output = "我是一个你的生活常识小助手，请问有什么能帮助你呢?"
    #print(f"模型输出：{assistant_output}\n")


def tongyi_QA_Model(user_input):
    global messages,assistant_output,new_speak
    
    if "有需要再找我喔" not in assistant_output:
        # 将用户问题信息添加到messages列表中
        messages.append({"role": "user", "content": user_input})
        assistant_output = get_response(messages).choices[0].message.content
        
        # 将大模型的回复信息添加到messages列表中
        messages.append({"role": "assistant", "content": assistant_output})
        #print(f"模型输出：{assistant_output}")
        
        
        if "有需要再找我喔" in assistant_output: #输出结果会在下一个问题前更新
            #print("清空对话")
            exit = assistant_output  
            New_session_init()  
            return exit
        
        return assistant_output
      
      
        



####英文版的，没有多轮对话
def tongyi_QA_Model_en(inputtext):
    client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=openAI_KEY,
    )

    completion = client.chat.completions.create(

    #model="google/gemini-2.5-pro-exp-03-25:free",
    model="qwen/qwen2.5-vl-32b-instruct:free",
    #model="meta-llama/llama-4-maverick:free",
    #model="nvidia/llama-3.1-nemotron-ultra-253b-v1:free",
    messages=[
        {
        "role": "user",
        "content": [
            {
            "type": "text",
            "text": inputtext
            }
        ]
        }
    ]
    )

    result = completion.choices[0].message.content
    #print(result)
    return result