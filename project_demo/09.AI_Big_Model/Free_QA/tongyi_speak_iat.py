# For prerequisites running the following sample, visit https://help.aliyun.com/document_detail/611472.html

import os
import time
from dashscope.audio.asr import *

import os,sys,time,threading,requests
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from API_KEY import *

import dashscope
dashscope.api_key = TONYI_key

from datetime import datetime

DIR_PATH_WAV = "./recorded_audio.wav"

rec_text = ''

def get_timestamp():
    now = datetime.now()
    formatted_timestamp = now.strftime("[%Y-%m-%d %H:%M:%S.%f]")
    return formatted_timestamp

class Callback(RecognitionCallback):
    def on_complete(self) -> None:
        print(get_timestamp() + ' Recognition completed')  # recognition complete

    def on_error(self, result: RecognitionResult) -> None:
        print('Recognition task_id: ', result.request_id)
        print('Recognition error: ', result.message)
        exit(0)

    def on_event(self, result: RecognitionResult) -> None:
        global rec_text
        sentence = result.get_sentence()
        if 'text' in sentence:
            #print(get_timestamp() + ' RecognitionCallback text: ', sentence['text'])
            if RecognitionResult.is_sentence_end(sentence):
                #print("Speaker:"+sentence['text'])
                rec_text = sentence['text']
                # print(get_timestamp() + 
                #     'RecognitionCallback sentence end, request_id:%s, usage:%s'
                #     % (result.get_request_id(), result.get_usage(sentence)))


callback = Callback()

recognition = Recognition(model=TONYI_API_IAT_MODEL,
                          format='wav',
                          sample_rate=16000,
                          # “language_hints”只支持paraformer-realtime-v2模型
                          language_hints=['zh', 'en','yue'],
                          callback=callback)


def rec_wav_music_Tongyi():
    global rec_text
    recognition.start()
    try:
        audio_data: bytes = None
        f = open(DIR_PATH_WAV, 'rb')
        if os.path.getsize(DIR_PATH_WAV):
            while True:
                audio_data = f.read(3200)
                if not audio_data:
                    break
                else:
                    recognition.send_audio_frame(audio_data)
                time.sleep(0.1)
        else:
            raise Exception(
                'The supplied file was empty (zero bytes long)')
        f.close()
    except Exception as e:
        raise e

    recognition.stop()
    
    return rec_text



