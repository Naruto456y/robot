from http import HTTPStatus
from urllib.parse import urlparse, unquote
from pathlib import PurePosixPath
import requests
from dashscope import ImageSynthesis
import os,sys,cv2,time


current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from API_KEY import *





def tongyi_image_creat(prompt = "一间有着精致窗户的花店，漂亮的木质门，摆放着花朵"):
    #print('----sync call, please wait a moment----')
    rsp = ImageSynthesis.call(api_key=TONYI_key,
                            model="wanx2.1-t2i-turbo",
                            prompt=prompt,
                            n=1,
                            size='640*640')
    #print('response: %s' % rsp)
    if rsp.status_code == HTTPStatus.OK:
        for result in rsp.output.results:
            file_name = PurePosixPath(unquote(urlparse(result.url).path)).parts[-1]
            with open('./Image_create/resized.jpg', 'wb+') as f:
                f.write(requests.get(result.url).content)
                
        imagedata = cv2.imread("./Image_create/resized.jpg")
        cv2.imshow('image',imagedata)
        cv2.waitKey(1)

        time.sleep(5.5)
        cv2.destroyAllWindows()
    else:
        print('sync_call Failed, status_code: %s, code: %s, message: %s' %
            (rsp.status_code, rsp.code, rsp.message))
        
        
        
