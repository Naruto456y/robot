"""
# file=输入文件名， cfile=输出名称
# 将compile.py文件复制到项目文件夹中，替换掉输入和输出的文件名
# 在终端运行python3 compile.py
"""
import py_compile
import os
py_compile.compile(file="car_speak_iat_en.py", cfile="car_speak_iat_en.pyc", optimize=-1)
py_compile.compile(file="car_tts_en.py", cfile="car_tts_en.pyc", optimize=-1)

#os.system("chmod +x add.pyc")
