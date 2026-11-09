import os,sys,time,threading,requests,base64
from openai import OpenAI


current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from API_KEY import *


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def tongyi_Image(imagetext):
    base64_image = encode_image("./SceneDescription/rec.jpg")
    client = OpenAI(
        api_key=TONYI_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    completion = client.chat.completions.create(
        model="qwen-vl-plus",  # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
        messages=[{"role": "user","content": [
                {"type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                {"type": "text", "text": imagetext},
                ]}]
        )
    #print(completion.model_dump_json())
    result = completion.choices[0].message.content
    print(result)

    return result

# tongyi_Image("这图片有什么")




def dogGPT_Image_en(inputtext):
    client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=openAI_KEY,
    )

    image_path = "./SceneDescription/rec.jpg"
    base64_image = encode_image(image_path)

    completion = client.chat.completions.create(

    model="qwen/qwen2.5-vl-32b-instruct:free",
    messages=[
        {
        "role": "user",
        "content": [
            {
            "type": "text",
            "text": inputtext
            },
            {
              "type": "image_url",
              "image_url": {"url": f"data:image/jpg;base64,{base64_image}"},
            }
        ]
        }
    ]
    )

    result = completion.choices[0].message.content
    #print(result)
    return result
    




