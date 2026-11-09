import os,sys
import requests
import dashscope,time
from subprocess import Popen
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from API_KEY import *


def tonyi_tts(strtts="今天天气怎么样？"):
    text = strtts
    response = dashscope.audio.qwen_tts.SpeechSynthesizer.call(
        model=TONYI_API_TTS_MODEL,
        api_key=TONYI_key,
        text=text,
        voice="Cherry",
    )
    audio_url = response.output.audio["url"]
    save_path = "answer.wav"  # 自定义保存路径

    try:
        response = requests.get(audio_url)
        response.raise_for_status()  # 检查请求是否成功
        with open(save_path, 'wb') as f:
            f.write(response.content)
        #print(f"音频文件已保存至：{save_path}")
        
        #播放音频 PLAY AUDIO
        proc = Popen("mplayer ./answer.wav", shell=True)
        proc.wait()
        time.sleep(0.5)
    except Exception as e:
        print(f"tts fail：{str(e)}")
        
        