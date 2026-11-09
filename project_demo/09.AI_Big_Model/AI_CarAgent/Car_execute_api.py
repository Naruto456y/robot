#执行层调用函数

from Car_base_control import * #基础动作
from Car_avoid_api import * #避障动作
from Car_music_api import * #在线音乐播放器
from Track_color_api import * #颜色追踪和巡线、跟随人脸接口、追踪物体api、场景描述

from Car_agent_Image import * #本地编写的智能体
from Car_agent_Online import Car_Tongyi_Image_Agent #在线的智能体

from Car_tongyi_tts import tonyi_tts #阿里的音频合成
from Car_tts import Car_Xinghou_speaktts #语音合成并播放
# from Car_image_api import Image_Describe

import os,sys,time,threading
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from API_KEY import *

exeute_relay = ''
#语音播放的标志
speak_execute_tts = 0
g_fail_ex = 0

def execute_Vioce():
    global exeute_relay,speak_execute_tts
    speak_execute_tts = 1
    if TTS_IAT_Tongyi:
        tonyi_tts(exeute_relay)
    else:
        Car_Xinghou_speaktts(exeute_relay)
    
    speak_execute_tts = 0

def safe_eval(expression):
    # 检查是否是单个标识符（函数名）
    if expression.isidentifier():
        raise SyntaxError(
            f"Function '{expression}' must be called with parentheses. "
            f"Use '{expression}()' instead of '{expression}'."
        )
    global  g_fail_ex
    g_fail_ex =0 #成功运行后，重置它
    return eval(expression)



def Car_decison_action(decision_str='决策层传入参数'):
    
    global speak_execute_tts,exeute_relay,g_fail_ex
    take_photo_agent() #拍照
    time.sleep(1)
        
    #decision_str = '把灯调成绿色，然后沿着天空的颜色线走，最后追踪个人脸。'
    print("Action:"+decision_str)    
    try: 
        if AI_Agent:
            agent_plan_execute = eval(Car_Tongyi_Image_Agent(decision_str))#线上的智能体
        else: 
            agent_plan_execute = eval(Car_Agent_Plan_Image(decision_str))#会调用本地的
            
        #print('智能体编排动作如下\n', agent_plan_output)
        exeute_relay = agent_plan_execute['response'] # 获取机器人想对我说的话
    except:
        display_text = "获取动作信息有误，请重试..."
        print(display_text)
        return
    
    if g_fail_ex == 0: #重试就不放音频了
        print("A:"+exeute_relay)
        execute_Vioce()
        # #开启语音线程,使其能边动边用
        # tts_thread = threading.Thread(target=execute_Vioce)
        # tts_thread.daemon = True  
        # tts_thread.start()
    
    
    for each in agent_plan_execute['function']: # 运行智能体规划编排的每个函数
        if xuanxin == 1:
            print("被唤醒打断了，请重新说指令吧")
            return 0 #已经触发打断
        try: 
            print('开始执行动作', each)
            safe_eval(each)
        except:
            g_fail_ex = g_fail_ex+1
            if g_fail_ex == 1: #动作执行失败
                print("Action try Start again!")
                os.system("pkill mplayer") #只有这次会播放线程音频
                time.sleep(0.5)#停顿下
                if TTS_IAT_Tongyi:
                    tonyi_tts('动作执行失败，准备再次尝试')
                else:
                    Car_Xinghou_speaktts('动作执行失败，准备再次尝试')
                return 1
            elif g_fail_ex>1:
                print("Action fail!")
                if TTS_IAT_Tongyi:
                    tonyi_tts('动作执行失败，提前结束任务')
                else:
                    Car_Xinghou_speaktts('动作执行失败，提前结束任务')
                g_fail_ex =0#清掉
                return 2
            
            
    
    while speak_execute_tts == 1:
        #print("wait")
        if xuanxin == 1:
            return 0 #已经触发打断


