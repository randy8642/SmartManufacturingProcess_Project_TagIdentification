import multiprocessing
import time
import requests
import numpy as np
import cv2
import paho.mqtt.client as mqtt
import json

from functions import getlocation, get_index


# PROCESS
def mqtt_client(que_id: multiprocessing.Queue, que_publish: multiprocessing.Queue):
    def on_connect(client, userdata, flags, rc):
        print("Connected with result code " + str(rc))

        client.subscribe("Label")

    def on_message(client, userdata, msg):
        # 轉換編碼utf-8才看得懂中文
        id_msg = msg.payload.decode('utf-8')
        que_id.put(id_msg)

    ip = json.load(open('./data/connect_config.json', mode='r'))['mqtt']['ip']
    port = json.load(open('./data/connect_config.json', mode='r'))['mqtt']['port']

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set("tracking", "xxxx")
    client.connect(ip, port, 60)

    # client.loop_forever()
    while True:
        client.loop()

        if not que_publish.empty():
            res = que_publish.get()
            topic = res['topic']
            msg = res['msg']

            client.publish(topic, payload=msg, qos=0)


def get_frame(que: multiprocessing.Queue):
  
    # # ONLY USE FOR TESTING
    # cap = cv2.VideoCapture('./src/output_concat_Trim.mp4')
    # while(True):

    #     ret, frame = cap.read()
    #     if not ret:
    #         break

    #     que.put(frame)
    #     time.sleep(0.02)

    # REAL
    url = json.load(open('./data/connect_config.json', mode='r'))['http url']

    while True:
        time.sleep(0.5)
        r = requests.get(url, stream=True)
        if(r.status_code == 200):
            bytes = bytes()
            for chunk in r.iter_content(chunk_size=1024):
                bytes += chunk
                a = bytes.find(b'\xff\xd8')
                b = bytes.find(b'\xff\xd9')
                if a != -1 and b != -1:
                    jpg = bytes[a:b+2]
                    bytes = bytes[b+2:]
                    frame = cv2.imdecode(np.fromstring(
                        jpg, dtype=np.uint8), cv2.IMREAD_COLOR)

                    que.put(frame)

        else:
            print("Received unexpected status code {}".format(r.status_code))


def track(que_frame: multiprocessing.Queue, que_Id: multiprocessing.Queue, que_publish: multiprocessing.Queue):
    id_list = []
    pre_img = None
    pre_boxs = np.empty([0, 5])

    while True:
        if not que_Id.empty():
            res_id = que_Id.get()
            id_list.append(res_id)
            print(id_list)

        if not que_frame.empty():
            res_frame = que_frame.get()

            next_img = cv2.cvtColor(res_frame, cv2.COLOR_BGR2GRAY)
            # next_img = cv2.GaussianBlur(next_img, (3, 3), 0)

            if pre_img is None:
                pre_img = next_img
                continue

            vis = cv2.absdiff(next_img, pre_img)

            ret, th = cv2.threshold(vis, 50, 255, cv2.THRESH_BINARY)
            dilated = cv2.dilate(th, None, iterations=1)
            contours, hierarchy = cv2.findContours(
                dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            boxes = []
            for n_contour, contour in enumerate(contours):

                x, y, w, h = cv2.boundingRect(contour)  # 該最大contour的(x,y)位置及長寬
                # 太小的目標框不是物件
                if w < 60:
                    continue

                location = round(getlocation(x - w/2), ndigits=1)

                boxes.append([location, x, y, w, h])
            
            full_boxs = get_index(pre_boxs.copy(), boxes)
            
            # 物體到達追蹤終點
            if full_boxs.shape[0] > 0 and full_boxs[0, 0] > 330:
                # END - pop box
                full_boxs = np.delete(full_boxs, 0, 0)                
                que_publish.put({
                    'topic': 'NckuMeCloudLab/Track',
                    'msg': f'{id_list[0]},-1'
                })
                id_list.pop(0)

            # 繪圖(實際運作時可刪除)
            for n, (loc, x, y, w, h) in enumerate(full_boxs):
                x, y, w, h = int(x), int(y), int(w), int(h)
                #cv2.drawContours(res_frame, contour, -1, (0, 255, 0), 2)
                cv2.rectangle(res_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(res_frame, f'loc {loc}cm', (x, y-5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                # cv2.putText(res_frame, f'index', (x+30, y+30),
                #             cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                # cv2.putText(res_frame, f'{n+1}', (x+30, y+70),
                #             cv2.FONT_HERSHEY_SIMPLEX, 1.7, (0, 0, 255), 2)
                cv2.putText(res_frame, f'ID', (x+30, y+30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
                cv2.putText(res_frame, f'{id_list[n]}', (x+30, y+70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

            # 發送新的位置
            for n, ((loc, *_), (pre_loc, *_)) in enumerate(zip(full_boxs, pre_boxs)):
                if loc == pre_loc:
                    continue

                # msg=> 工件編號,位置(cm)
                que_publish.put({
                    'topic': 'NckuMeCloudLab/Track',
                    'msg': f'{id_list[n]},{loc}'
                })

            cv2.imshow('', cv2.resize(res_frame, (1500,200)))
            cv2.waitKey(1)

            pre_boxs = full_boxs


def main():
    que_mqtt_objectId = multiprocessing.Queue()
    que_request_img = multiprocessing.Queue()
    que_publish = multiprocessing.Queue()

    process_list = list()

    # http stream get frame
    p = multiprocessing.Process(target=get_frame, args=[que_request_img])
    p.name = 'get_frame_from_httpStream'
    process_list.append(p)

    # tracking
    p = multiprocessing.Process(
        target=track, args=[que_request_img, que_mqtt_objectId, que_publish])
    p.name = 'get_frame_from_httpStream'
    process_list.append(p)

    # mqtt
    p = multiprocessing.Process(target=mqtt_client, args=[
                                que_mqtt_objectId, que_publish])
    p.name = 'mqtt'
    process_list.append(p)

    # 開始執行
    p: multiprocessing.Process
    for p in process_list:
        p.start()


if __name__ == '__main__':
    main()
