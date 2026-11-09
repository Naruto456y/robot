#功能主要入口 英文版 Main entrance English version of the function

from Car_audio import * #唤醒并录音 Wake up and record

from car_speak_iat_en import rec_wav_music_en #音频识别 Audio recognition
from car_tts_en import Xinghou_speaktts #语音合成并播放 Speech synthesis and playback


from Car_decision_agent import * #决策层智能体 Decision making intelligent agent
from Car_execute_api import Car_decison_action #执行层智能体执行函数 Execution layer intelligent agent executes functions
from Car_base_control import Car_Reset,xuanxin,Get_Fail_Falg

import os,sys,time,threading,requests
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import subprocess

#打断后kill
def PIDkill_process(KillPath):
        try:
            # 使用pgrep查找脚本
            result = subprocess.run(['pgrep', '-f', KillPath], capture_output=True, text=True, check=True)
            pids = result.stdout.strip().split('\n')
            # 遍历找到的所有PID
            for pid in pids:
                try:
                    # 终止进程
                    subprocess.run(['kill', pid], check=True)
                    print(f"Process {pid} has been terminated.")
                except subprocess.CalledProcessError:
                    print(f"Failed to terminate process {pid}.")
        except subprocess.CalledProcessError:
            pass
            #print("No matching processes found.")


response = ''
agent_plan_output = ''


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
        
        
        try: 
            if Get_Fail_Falg() == 2:#预判的失败动作 Anticipated failure actions
                time.sleep(2)
                Xinghou_speaktts('Unable to implement task steps, end task prematurely')
                break #提前结束任务  End the task ahead of schedule
            
            
            print('Start executing action', each)
            result = eval(each)
            
            if result == 1:
                result = eval(each)
                if result == 2:
                    break #提前结束任务  End the task ahead of schedule
        except:
            continue
    

def play_agent_image():
    print("start")
    global response,agent_plan_output,xuanxin
    while True:
        if detect_keyword():
            
            xuanxin = 1
            os.system("pkill mplayer") 
            PIDkill_process('./AI_CarAgent_en/Track_color_Follow_api.py')
            PIDkill_process('./AI_CarAgent_en/Track_color_line_api.py')
            PIDkill_process('./AI_CarAgent_en/Track_Face_Follow_api.py')
            PIDkill_process('./AI_CarAgent_en/Track_Food_api.py')
            Car_Reset() #小车复位 Car reset
            time.sleep(.2)
            os.system('mplayer ./ihere_en.wav') 
            time.sleep(0.5)
            
            if os.path.exists(SAVE_FILE):
                 os.remove(SAVE_FILE)
            time.sleep(0.2)

            start_recording()

            time.sleep(0.2)
            rectext = rec_wav_music_en()#进行语音识别 Perform speech recognition
            #rectext = 'what do you see'
            
            if rectext != "":
                print("Q:"+ rectext)
                try:
                    agent_plan_output = eval(Car_decision_Plan(rectext)) 
                    response = agent_plan_output['response']
                except:
                    display_text = "Decision failed, please try again..."
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
            play_agent_image()
        except:
            Car_Reset()
    else:
        print("Please restart the program. If the problem is not resolved, check if the network configuration can access the internet")
        while True:
            time.sleep(0.1)

