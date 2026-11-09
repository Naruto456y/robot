import os
from http import HTTPStatus
from dashscope import Application

import os,sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from API_KEY import *



def Car_tonyi_agent_online(angettext = '在线智能体'):
    response = Application.call(
        # 若没有配置环境变量，可用百炼API Key将下行替换为：api_key="sk-xxx"。但不建议在生产环境中直接将API Key硬编码到代码中，以减少API Key泄露风险。
        api_key=TONYI_key,
        app_id=Online_Action_ID,# 替换为实际的应用 ID
        prompt= angettext)

    if response.status_code != HTTPStatus.OK:
        print(f'request_id={response.request_id}')
        print(f'code={response.status_code}')
        print(f'message={response.message}')
        print(f'请参考文档：https://help.aliyun.com/zh/model-studio/developer-reference/error-code')
        return ''
    else:
        #print(response.output.text) #成功输出
        return response.output.text