import cv2
import time

Path_video = "./VideoDescription/record_video.mp4"

def record_video():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("open camera fail!")
        exit()
        
    frame_width = 640
    frame_height = 480
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)


    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(Path_video, fourcc, 20.0, (frame_width, frame_height))

    start_time = time.time()
    record_seconds = 5  #录制时长 Recording duration

    print("start recording")

    while cap.isOpened():
        ret, frame = cap.read()
        
        if not ret:
            print("fail")
            break
        
        out.write(frame)
        
        elapsed = time.time() - start_time
        if elapsed >= record_seconds :
            break

    print(f"Recording completed! ({elapsed:.2f}s)")

    cap.release()
    out.release()
    cv2.destroyAllWindows()
    
    
def play_video():
    cap = cv2.VideoCapture(Path_video)

    if not cap.isOpened():
        print(f"open fail: {Path_video}")
        exit()

    while cap.isOpened():
        ret, frame = cap.read()
        if ret:
            cv2.imshow('Video Playback', frame)
            if cv2.waitKey(40) == 27:
                break
        else: 
            print("end!")
            break

    cap.release()
    cv2.destroyAllWindows()