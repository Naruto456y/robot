from openai import OpenAI
import os,sys,time,threading,requests

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from API_KEY import *


def tongyi_QA_Model(strtext):
    client = OpenAI(
        api_key=TONYI_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    completion = client.chat.completions.create(
        # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
        model="qwen-plus",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": strtext},
        ],
    )
    #print(completion.model_dump_json())
    result = completion.choices[0].message.content
    #print(result)
    return result


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

    
    