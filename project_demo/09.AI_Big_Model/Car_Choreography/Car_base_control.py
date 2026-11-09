from McLumk_Wheel_Sports import *
import time,os,subprocess
from Car_tts import Car_Xinghou_speaktts

from car_tts_en import Xinghou_speaktts

def is_mplayer_playing():
    # 检查mplayer进程是否存在 Check if the mplayer process exists
    try:
        # 使用pgrep查找mplayer进程 Using pgrep to search for mplayer processes
        result = subprocess.check_output(['pgrep', '-l', 'mplayer'])
        if not result:
            return False
        return True
    except subprocess.CalledProcessError:
        return False

#前进 forward
def Car_Forword(speed=40,mytime=1):
    move_forward(speed)
    time.sleep(mytime)
    stop_robot()
    time.sleep(0.2)

    
#后退 back
def Car_back(speed=40,mytime=1):
    move_backward(speed)
    time.sleep(mytime)
    stop_robot()
    time.sleep(0.2)
    

#原地左转 Turn left in place
def Car_left(speed=50,mytime=1):
    rotate_left(speed)
    time.sleep(mytime)
    stop_robot()
    time.sleep(0.2)


#原地右转 Turn right in place
def Car_right(speed=50,mytime=1):
    rotate_right(speed)
    time.sleep(mytime)
    stop_robot()
    time.sleep(0.2)
    
    
#左平移 Left translation
def Car_left_translation(speed=45,mytime=1):
    move_left(speed)
    time.sleep(mytime)
    stop_robot()
    time.sleep(0.2)
    
    
    
#右平移 Right translation
def Car_right_translation(speed=45,mytime=1):
    move_right(speed)
    time.sleep(mytime)
    stop_robot()
    time.sleep(0.2)
    
    
##舵机动作 Servo motor action
#点头 nod one's head
def Car_servo_nod():
    for i in range(2):
        bot.Ctrl_Servo(2, 25)
        time.sleep(0.3)
        bot.Ctrl_Servo(2, 100)
        time.sleep(0.3)
    bot.Ctrl_Servo(2, 25) #恢复中位 Restore median


#摇头 Shake one's head
def Car_servo_sayno():
    for i in range(2):
        bot.Ctrl_Servo(1, 60)
        time.sleep(0.3)
        bot.Ctrl_Servo(1, 120)
        time.sleep(0.3)
    bot.Ctrl_Servo(1, 90) #恢复中位 Restore median
    
    
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from API_KEY import TTS_IAT_Tongyi
#获取障碍物距离 Obtain obstacle distance
def Get_dis_obstacle():
    time.sleep(1)
    bot.Ctrl_Ulatist_Switch(1) #开启测距 Enable distance measurement
    time.sleep(0.1)
    for i in range(3):
        diss_H =bot.read_data_array(0x1b,1)[0]
        diss_L =bot.read_data_array(0x1a,1)[0]
        dis = diss_H << 8 | diss_L
        time.sleep(0.1)
    bot.Ctrl_Ulatist_Switch(0) #关闭测距 Turn off distance measurement
    
    if dis<250:
        #播报障碍物的距离 Report the distance of obstacles
        tts_text="障碍物的距离为:"+str(dis)+"mm"
        print("A:"+tts_text)
        while is_mplayer_playing():  #等待音频播放完成再播放 Wait for the audio playback to complete before playing again
            pass
        if TTS_IAT_Tongyi:
            tonyi_tts(tts_text)
        else:
            Car_Xinghou_speaktts(tts_text)
            
    else:
        while is_mplayer_playing():  #等待音频播放完成再播放 Wait for the audio playback to complete before playing again
            pass
        os.system("mplayer ./Car_Choreography/noobstacle.mp3 < /dev/null > /dev/null 2>1 &")
        print("A:没有检测到障碍物")
        time.sleep(0.5)
        
        
#获取障碍物距离 Obtain obstacle distance
def Get_dis_obstacle_en():
    time.sleep(1)
    bot.Ctrl_Ulatist_Switch(1) #开启测距 Enable distance measurement
    time.sleep(0.1)
    for i in range(3):
        diss_H =bot.read_data_array(0x1b,1)[0]
        diss_L =bot.read_data_array(0x1a,1)[0]
        dis = diss_H << 8 | diss_L
        time.sleep(0.1)
    bot.Ctrl_Ulatist_Switch(0) #关闭测距 Turn off distance measurement
    
    if dis<250:
        #播报障碍物的距离 Report the distance of obstacles
        tts_text="The distance of the obstacle is:"+str(dis)+"mm"
        print("A:"+tts_text)
        while is_mplayer_playing():  #等待音频播放完成再播放 Wait for the audio playback to complete before playing again
            pass
        
        Xinghou_speaktts(tts_text)
            
    else:
        while is_mplayer_playing():  #等待音频播放完成再播放 Wait for the audio playback to complete before playing again
            pass
        os.system("mplayer ./Car_Choreography/noobstacle_en.mp3 < /dev/null > /dev/null 2>1 &")
        print("A:No obstacles detected")
        time.sleep(0.5)


#控制RGB灯颜色 Control RGB light color
def Car_RGB_Control(R,G,B):
    bot.Ctrl_WQ2812_brightness_ALL(R,G,B)

#关闭RGB灯 Turn off RGB lights
def Close_RGB():
    bot.Ctrl_WQ2812_ALL(0,7)
    
    
#小车复位操作 Car reset operation
def Car_Reset():
    Close_RGB()
    bot.Ctrl_Ulatist_Switch(0) #关闭测距 Turn off distance measurement
    bot.Ctrl_Servo(1, 90) 
    bot.Ctrl_Servo(2, 25)
    stop_robot()
    
    