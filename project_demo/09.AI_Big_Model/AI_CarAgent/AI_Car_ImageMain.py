#功能主要入口

from Car_audio import * #唤醒并录音

from Car_speak_iat import * #音频识别
from Car_tts import Car_Xinghou_speaktts #语音合成并播放

from Car_tongyi_speak_iat import rec_wav_music_Tongyi #阿里的音频识别
from Car_tongyi_tts import tonyi_tts #阿里的音频合成

from Car_decision_agent import * #决策层智能体
from Car_execute_api import Car_decison_action #执行层智能体执行函数
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
        
        try: 
            if Get_Fail_Falg() == 2:#预判的失败动作
                time.sleep(2)
                if TTS_IAT_Tongyi:
                    tonyi_tts('无法实现任务步骤，提前结束任务')
                else:
                    Car_Xinghou_speaktts('无法实现任务步骤，提前结束任务')
                break #提前结束任务 
            
            
            print('开始执行动作', each)
            result = eval(each)
            
            if result == 1:
                result = eval(each)
                if result == 2:
                    break #提前结束任务 
        except:
            continue
    

def play_agent_image():
    print("start")
    global response,agent_plan_output,xuanxin
    while True:
        if detect_keyword():
            #打断处理
            xuanxin = 1
            os.system("pkill mplayer") 
            PIDkill_process('./AI_CarAgent/Track_color_Follow_api.py')
            PIDkill_process('./AI_CarAgent/Track_color_line_api.py')
            PIDkill_process('./AI_CarAgent/Track_Face_Follow_api.py')
            PIDkill_process('./AI_CarAgent/Track_Food_api.py')
            Car_Reset() #小车复位
            time.sleep(.2)
            os.system('mplayer ./ihere.wav < /dev/null > /dev/null 2>1 &') #播放我在
            time.sleep(0.5)
            
            
            #先把存在的录音删掉
            if os.path.exists(SAVE_FILE):
                os.remove(SAVE_FILE)
            time.sleep(0.2)

            start_recording()

            time.sleep(0.2)
            if TTS_IAT_Tongyi:
                rectext = rec_wav_music_Tongyi()#进行语音识别
            else:
                rectext = rec_wav_music()#进行语音识别
            
            #rectext = '把灯调成黄色，休息1s点点头,休息1s摇摇头,休息1s摇摇头,休息1s点点头,告诉我前方障碍物的距离，然后跟随绿色的物体，再巡蓝线，追踪人脸，最后播放一首周董的稻香。'

            #rectext = '描述下黄色木块左边的物体，然后追踪它'
            
            if rectext != "":
                print("Q:"+ rectext)
                try:
                    agent_plan_output = eval(Car_decision_Plan(rectext)) #决策放在了本地了
                    response = agent_plan_output['response'] # 获取机器人想对我说的话
                except:
                    display_text = "决策失败，请重试..."
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
                print('"没有识别到任何信息,请重试"')
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
            play_agent_image()
        except:
            Car_Reset() #小车复位 
    else:
        print("请重启程序，如果问题没解决，检查网络配置是否能上网")
        while True:
            time.sleep(0.1)

