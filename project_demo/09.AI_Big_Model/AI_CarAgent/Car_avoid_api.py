#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import sys
sys.path.append('/home/pi/project_demo/lib')
#导入麦克纳姆小车驱动库 Import Mecanum Car Driver Library
from McLumk_Wheel_Sports import *



def car_avoid_api(fardis = 200,Stopflag = 1):
    speed = 20  # Set vehicle speed
    bot.Ctrl_Ulatist_Switch(1)
    time.sleep(0.1)  # 给超声波传感器一点时间来测量 Give the ultrasonic sensor some time to measure
    
    while True:
        # 读取超声波传感器的距离 Reading distance from ultrasonic sensor
        diss_H =bot.read_data_array(0x1b,1)[0]
        diss_L =bot.read_data_array(0x1a,1)[0]
        dis = diss_H << 8 | diss_L 

        # 打印距离 Printing distance
        # print(f"Ultrasonic Distance: {dis} mm")
        time.sleep(0.05)  # 每隔1秒读取一次距离 Read the distance every 1 second

        if dis > fardis:
            #print(f"Obstacle is very close, distance: {dis} mm")
            move_forward(speed)
            time.sleep(0.1)
        

        else:
            if Stopflag == 1: #有停下来的要求
                # print("istopping")
                stop_robot()
                time.sleep(0.2)
                stop_robot()
                
            bot.Ctrl_Ulatist_Switch(0) #关闭测距
            return



