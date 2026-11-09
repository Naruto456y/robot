# 智能小车主程序入口-中文版

from Car_audio import * #唤醒并录音
from Car_base_control import * #基础动作
from Car_avoid_api import * #避障动作
from Car_music_api import * #在线音乐播放器

from Car_speak_iat import * #音频识别
from Car_tts import Car_Xinghou_speaktts #语音合成并播放

from Car_tongyi_speak_iat import rec_wav_music_Tongyi #阿里的音频识别
from Car_tongyi_tts import tonyi_tts #阿里的音频合成

from Car_agent import * #动作编排智能体
from Car_agent_Online import *

import os,sys,time,threading,requests
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)




response = ''
agent_plan_output = ''
xuanxin = 0 #唤醒标志

def Speak_Vioce():
    global response
    if TTS_IAT_Tongyi:
        tonyi_tts(response)
    else:
        Car_Xinghou_speaktts(response)
    
    
#智能体线程
def Agent_Contorl():
    global agent_plan_output,xuanxin
    xuanxin = 0
    for each in agent_plan_output['function']: # 运行智能体规划编排的每个函数
        if xuanxin == 1:
            return #已经触发打断
        
        print('开始执行动作', each)
        try: 
            eval(each)
        except:
            continue
    

def play_agent():
    print("start")
    global response,agent_plan_output,xuanxin
    while True:
        if detect_keyword():
            #打断处理
            xuanxin = 1
            os.system("pkill mplayer") 
            Car_Reset() #小车复位
            time.sleep(.2)
            
            #先把存在的录音删掉
            if os.path.exists('./myrec.wav'):
                os.remove('./myrec.wav')
            time.sleep(0.2)

            start_recording()

            time.sleep(0.2)
            if TTS_IAT_Tongyi:
                rectext = rec_wav_music_Tongyi()#进行语音识别
            else:
                rectext = rec_wav_music()#进行语音识别
            
            #rectext = '碰到了前面15cm的物体停下来，然后左转半圈'

            if rectext != "":
                print("Q:"+ rectext)
                try:
                    if AI_Agent:
                        agent_plan_output = eval(Car_tonyi_agent_online(rectext))#线上的智能体
                    else: 
                        agent_plan_output = eval(Car_Agent_Plan(rectext))#会调用本地的
                        
                    
                    #print('智能体编排动作如下\n', agent_plan_output)
                    response = agent_plan_output['response'] # 获取机器人想对我说的话
                    ###print('开始语音合成并播放：'+response)  
                except:
                    display_text = "获取动作信息有误，请重试..."
                    print(display_text)
                    continue
                
                print("A:"+response)


                #开启语音线程,使其能边动边用
                tts_thread = threading.Thread(target=Speak_Vioce)
                tts_thread.daemon = True  
                tts_thread.start()
                
                #开启动作执行线程
                tts_thread = threading.Thread(target=Agent_Contorl)
                tts_thread.daemon = True  
                tts_thread.start()
                

            else :
                print("没有识别到任何信息,请重试")
            if rectext == 0:
               break




if __name__ == '__main__':
    net = False
    try:
        html = requests.get("http://www.baidu.com", timeout=3)
        net = True
    except Exception as e:
        print(f"Network check failed: {e}")
        net = False
    if net:  
        Car_Reset() #小车复位  
        try:
            play_agent()
        except:
            Car_Reset() #小车复位  
    else:
        print("请重启程序，如果问题没解决，检查网络配置是否能上网")
        while True:
            time.sleep(0.1)