#Execute layer calling function

from Car_base_control import * #基础动作 Basic actions
from Car_avoid_api import * #避障动作 Obstacle avoidance action
from Car_music_api import * #在线音乐播放器 Online music player
from Track_color_api import * #颜色追踪和巡线、跟随人脸接口 追踪物体api Tracking Object API  Color tracking and line tracing, following face interface

from Car_agent_Image import * #本地编写的智能体 Locally written intelligent agents
from Car_dify_API import Car_Agent_Plan_Image_Dify #引入本地dify里面的智能体 Introduce intelligent agents from local dify
 
from car_tts_en import Xinghou_speaktts #语音合成 speech synthesis


import os,sys,time,threading
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from API_KEY import *

exeute_relay = ''
#语音播放的标志 Signs for voice playback
speak_execute_tts = 0
g_fail_ex = 0


def execute_Vioce():
    global exeute_relay,speak_execute_tts
    speak_execute_tts = 1
    Xinghou_speaktts(exeute_relay)
    
    speak_execute_tts = 0

def safe_eval(expression):
    if expression.isidentifier():
        raise SyntaxError(
            f"Function '{expression}' must be called with parentheses. "
            f"Use '{expression}()' instead of '{expression}'."
        )
    global  g_fail_ex
    g_fail_ex =0 #成功运行后，重置它 #After successful operation, reset it
    return eval(expression)



def Car_decison_action(decision_str='Decision makers input parameters'):
    
    global speak_execute_tts,exeute_relay,g_fail_ex
    take_photo_agent() #拍照 take pictures
    time.sleep(1)
    
    print("Action:"+decision_str)    
    try: 
        if DIFY_SWITCH ==False:
            agent_plan_execute = eval(Car_Agent_Plan_Image(decision_str))
        else:
            agent_plan_execute = eval(Car_Agent_Plan_Image_Dify(decision_str)) #dify
            
        exeute_relay = agent_plan_execute['response'] 
    except:
        display_text = "Error in obtaining action information, please try again..."
        print(display_text)
        return
    
    if g_fail_ex == 0: #重试就不放音频了 If you retry, you won't play the audio anymore
        print("A:"+exeute_relay)
        execute_Vioce()
        #Activate the voice thread so that it can be used while moving
        # tts_thread = threading.Thread(target=execute_Vioce)
        # tts_thread.daemon = True  
        # tts_thread.start()
    
    
    for each in agent_plan_execute['function']: # 运行智能体规划编排的每个函数 Run each function of intelligent agent planning and orchestration
        if xuanxin == 1:
            print("Interrupted by wake-up, please rephrase the command")
            return 
        
        try: 
            print('Start executing action', each)
            eval(each)
        except:
            g_fail_ex = g_fail_ex+1
            if g_fail_ex == 1: #动作执行失败 Action execution failed
                print("Action try Start again!")
                os.system("pkill mplayer") #只有这次会播放线程音频 Only this time will thread audio be played
                time.sleep(0.5)
                Xinghou_speaktts('Action execution failed, prepare to try again')
                return 1
            elif g_fail_ex>1:
                print("Action fail!")
                Xinghou_speaktts('Action execution failed, end task prematurely')
                g_fail_ex =0
                return 2
    
    while speak_execute_tts == 1:
        #print("wait")
        if xuanxin == 1:
            return #已经触发打断 Interruption has been triggered
