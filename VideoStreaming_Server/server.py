from flask import Flask, Response
import cv2
import threading
import time
import numpy as np
import json
from Camera import rtsp_cam as Cam


app = Flask(__name__)

now_frame = None
readTime = time.time() #sec
info = ''

def updateFrame():
    print('start thread')
    cap = Cam()    

    global now_frame
    global readTime
    global info

    # READ JSON
    json_data = json.load(open('./config/cameras_config.json', 'r'))
    info = json_data['camera']
    camera_cnt = len(info)   
    del json_data

    while True:        
        
        if (time.time() - readTime > 30) and (cap.starting == True): # sec
            print('close')
            cap.close()
            time.sleep(1)
        elif (time.time() - readTime < 30) and (cap.starting == False):
            print('start')
            cap.start()
        
        ####
        if cap.starting:
            success, rawframe = cap.read()

            if not success:
                continue
            images = [None] * camera_cnt
            single_width = rawframe.shape[1] // camera_cnt
            for n in range(len(info)):
                images[n] = rawframe[:, n * single_width:(n + 1) * single_width, :]
            frame = concatImage(images)

            # 更新影格     
            now_frame = frame        

def gen_frames():  
    global now_frame
    global readTime
    while True:
        readTime = time.time()
        if now_frame is None:
            break
        ret, buffer = cv2.imencode('.jpg', now_frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result


def concatImage(images):
    global info
    for n, img in enumerate(images):
        src_contour = info[n]['perspective']['src']
        width = info[n]['perspective']['width']
        hight = info[n]['perspective']['hight']

        pts1 = np.float32(src_contour)
        pts2 = np.float32([(0, 0), (0, hight), (width, hight), (width, 0)])
        M = cv2.getPerspectiveTransform(pts1, pts2)
        dst = cv2.warpPerspective(img, M, (width, hight))
        images[n] = dst


    for n, img in enumerate(images):
        front = info[n]['concat_x']['front']
        back = info[n]['concat_x']['back']

        images[n] = img[:, front:back, :]

    return cv2.hconcat(images)


# @app.route('/')
# def index():
#     return render_template('index.html')

@app.route('/stream')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == "__main__":
    j = threading.Thread(target=updateFrame)
    j.start()

    app.run(debug=True)
    j.join()