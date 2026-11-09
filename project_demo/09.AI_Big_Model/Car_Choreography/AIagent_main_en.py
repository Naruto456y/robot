# 智能小车主程序入口 Intelligent car main program entrance

from Car_audio import * #唤醒并录音 Wake up and record
from Car_base_control import * #基础动作 Basic actions
from Car_avoid_api import * #避障动作 Obstacle avoidance action
from Car_music_api import * #在线音乐播放器 Online music player
from Car_agent_en import * #动作编排智能体 Action choreography agent

from car_speak_iat_en import rec_wav_music_en #音频识别 Audio recognition
from car_tts_en import Xinghou_speaktts #语音合成并播放 Speech synthesis and playback

import os,sys,time,threading,requests
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)




response = ''
agent_plan_output = ''
xuanxin = 0 #唤醒标志 Wake up flag

def Speak_Vioce():
    global response
    Xinghou_speaktts(response)
    
    
#智能体线程 Intelligent agent thread
def Agent_Contorl():
    global agent_plan_output,xuanxin
    xuanxin = 0
    for each in agent_plan_output['function']: # 运行智能体规划编排的每个函数 Run each function of intelligent agent planning and orchestration
        if xuanxin == 1:
            return #已经触发打断 Interruption has been triggered
        
        print('Start executing action', each)
        try: 
            eval(each)
        except:
            continue
    

def play_agent():
    print("start")
    global response,agent_plan_output,xuanxin
    while True:
        if detect_keyword():
            #打断处理 Interrupt processing
            xuanxin = 1
            os.system("pkill mplayer") 
            Car_Reset() #小车复位 Car reset
            time.sleep(.2)
            
            #先把存在的录音删掉 First, delete the existing recording
            if os.path.exists('./myrec.wav'):
                os.remove('./myrec.wav')
            time.sleep(0.2)

            start_recording()

            time.sleep(0.2)
            rectext = rec_wav_music_en()#Perform speech recognition
            
            if rectext != "":
                print("Q:"+ rectext)
                try:
                    agent_plan_output = eval(Car_Agent_Plan(rectext))
                    
                   
                    response = agent_plan_output['response'] # 获取机器人想对我说的话 Get what the robot wants to say to me
                    
                except:
                    display_text = "Error in obtaining action information, please try again..."
                    print(display_text)
                    continue
                
                print("A:"+response)


                #开启语音线程,使其能边动边用 Activate the voice thread so that it can be used while moving
                tts_thread = threading.Thread(target=Speak_Vioce)
                tts_thread.daemon = True  
                tts_thread.start()
                
                #开启动作执行线程 Open the action execution thread
                tts_thread = threading.Thread(target=Agent_Contorl)
                tts_thread.daemon = True  
                tts_thread.start()
                

            else :
                print("No information was recognized, please try again")
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
        Car_Reset() 
        try:
            play_agent()
        except:
            Car_Reset() 
    else:
        print("Please restart the program. If the problem is not resolved, check if the network configuration can access the internet")
        while True:
            time.sleep(0.1)