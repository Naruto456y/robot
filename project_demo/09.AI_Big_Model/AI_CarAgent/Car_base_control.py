from McLumk_Wheel_Sports import *
import time,os,subprocess
from Car_tts import Car_Xinghou_speaktts
from Car_tongyi_tts import tonyi_tts #阿里的音频合成

import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from API_KEY import TTS_IAT_Tongyi

xuanxin = 0 #唤醒标志
g_fail = 0 #动作执行失败标志 一般是大模型反馈的函数接口

# 设置可以预知的必定失败任务
def Set_Fail_Flag(flag):
    global g_fail
    g_fail = 2
    
def Get_Fail_Falg():
    global g_fail
    return g_fail

def is_mplayer_playing():
    # 检查mplayer进程是否存在
    try:
        # 使用pgrep查找mplayer进程
        result = subprocess.check_output(['pgrep', '-l', 'mplayer'])
        if not result:
            return False
        return True
    except subprocess.CalledProcessError:
        return False

#前进
def Car_Forword(speed=40,mytime=1):
    move_forward(speed)
    time.sleep(mytime)
    stop_robot()
    time.sleep(0.2)

    
#后退
def Car_back(speed=40,mytime=1):
    move_backward(speed)
    time.sleep(mytime)
    stop_robot()
    time.sleep(0.2)
    

#原地左转 1圈
def Car_left(speed=50,mytime=1):
    rotate_left(speed)
    time.sleep(mytime)
    stop_robot()
    time.sleep(0.2)


#原地右转 1圈
def Car_right(speed=50,mytime=1):
    rotate_right(speed)
    time.sleep(mytime)
    stop_robot()
    time.sleep(0.2)
    
    
#左平移
def Car_left_translation(speed=45,mytime=1):
    move_left(speed)
    time.sleep(mytime)
    stop_robot()
    time.sleep(0.2)
    
    
    
#右平移
def Car_right_translation(speed=45,mytime=1):
    move_right(speed)
    time.sleep(mytime)
    stop_robot()
    time.sleep(0.2)
    
    
##舵机动作
#点头
def Car_servo_nod():
    for i in range(2):
        bot.Ctrl_Servo(2, 25)
        time.sleep(0.3)
        bot.Ctrl_Servo(2, 100)
        time.sleep(0.3)
    bot.Ctrl_Servo(2, 25) #恢复中位


#摇头
def Car_servo_sayno():
    for i in range(2):
        bot.Ctrl_Servo(1, 60)
        time.sleep(0.3)
        bot.Ctrl_Servo(1, 120)
        time.sleep(0.3)
    bot.Ctrl_Servo(1, 90) #恢复中位
    

#获取障碍物距离
def Get_dis_obstacle():
    time.sleep(1)
    bot.Ctrl_Ulatist_Switch(1) #开启测距
    time.sleep(0.1)
    for i in range(3):
        diss_H =bot.read_data_array(0x1b,1)[0]
        diss_L =bot.read_data_array(0x1a,1)[0]
        dis = diss_H << 8 | diss_L
        time.sleep(0.1)
    bot.Ctrl_Ulatist_Switch(0) #关闭测距
    
    if dis<250:
        #播报障碍物的距离
        tts_text="障碍物的距离为:"+str(dis)+"mm"
        print("A:"+tts_text)
        while is_mplayer_playing():  #等待音频播放完成再播放
            pass
        if TTS_IAT_Tongyi:
            tonyi_tts(tts_text)
        else:
            Car_Xinghou_speaktts(tts_text)
            
    else:
        while is_mplayer_playing():  #等待音频播放完成再播放
            pass
        os.system("mplayer ./AI_CarAgent/noobstacle.mp3 < /dev/null > /dev/null 2>1 &")
        print("A:没有检测到障碍物")
        time.sleep(0.5)
        


#控制RGB灯颜色
def Car_RGB_Control(R,G,B):
    bot.Ctrl_WQ2812_brightness_ALL(R,G,B)

#关闭RGB灯
def Close_RGB():
    bot.Ctrl_WQ2812_ALL(0,7)
    
    
#小车复位操作
def Car_Reset():
    Close_RGB()
    bot.Ctrl_Ulatist_Switch(0) #关闭测距
    bot.Ctrl_Servo(1, 90) #恢复中位
    bot.Ctrl_Servo(2, 25) #恢复中位
    stop_robot()
    


import cv2
#打开摄像头，记录图片
def take_photo_agent():
    time.sleep(1) #等1s
    cap=cv2.VideoCapture(0)
    cap.set(3,320*2)
    cap.set(4,240*2)

    path = "./AI_CarAgent/"  
    ret, image = cap.read()
    filename = "rec"
    cv2.imwrite(path + filename + ".jpg", image)
    time.sleep(1)
    cap.release()
    print("Photos to record")
    print("camera close")


# def Image_Describe(tt = 1):
#     img = cv2.imread("./AI_CarAgent/rec.jpg")
#     cv2.imshow('image',img)
#     cv2.waitKey(1)
#     time.sleep(3)
#     cv2.destroyAllWindows()
    
