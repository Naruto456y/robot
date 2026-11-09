from Speech_Lib import Speech

mySpeech = Speech()

try:
    while 1:
        num = mySpeech.speech_read()
        if num !=999:
            print(num)
            mySpeech.void_write(num)
            num =999
except:
    mySpeech.__del__()
    print("串口关闭")