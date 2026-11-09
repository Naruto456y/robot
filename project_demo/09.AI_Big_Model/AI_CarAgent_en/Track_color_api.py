import sys,os
import time
import subprocess

#使用python打开，这样的效果会更好
def Track_Follow_color(strcolor='red'):
    process = subprocess.Popen(['python', './AI_CarAgent_en/Track_color_Follow_api.py',strcolor])
    while True:
        time.sleep(1)
        if process.poll() is not None:
            #print("颜色跟随程序已经结束")
            break
        # else:
        #     print("另一个程序还在运行")
            


def Track_line(colorline = 'red'):
    process = subprocess.Popen(['python', './AI_CarAgent_en/Track_color_line_api.py',colorline])
    while True:
        time.sleep(1)
        if process.poll() is not None:
            #print("颜色巡线程序已经结束")
            break
        
def Track_Face_Follow():
    process = subprocess.Popen(['python', './AI_CarAgent_en/Track_Face_Follow_api.py'])
    while True:
        time.sleep(1)
        if process.poll() is not None:
            #print("人脸跟随程序已经结束")
            break
        
def Tarck_Food(strname='Track Food of forword'):
    process = subprocess.Popen(['python', './AI_CarAgent_en/Track_Food_api.py',strname])
    while True:
        time.sleep(1)
        if process.poll() is not None:
            #print("物体追踪程序已经结束")
            break
        
def Image_Describe(str='what can you see'):
    process = subprocess.Popen(['python', './AI_CarAgent_en/Car_image_api_en.py',str])
    while True:
        time.sleep(1)
        if process.poll() is not None:
            #print("描述案例已经结束")
            break
        # else:
        #     print("另一个程序还在运行")