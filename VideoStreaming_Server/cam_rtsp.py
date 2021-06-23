import json
import multiprocessing
from multiprocessing.connection import Connection
import cv2
import numpy as np
import time


class Camera():
    def __init__(self) -> None:

        self.cameraDatas = json.load(open('./config/cameras_config.json'))['camera']
        self.cameraCnt = len(self.cameraDatas)

        self.width = 640
        self.heigth = 480
        
        self.starting = False


        pass
    
    
    def start(self):
        if self.starting:
            return
            
        ###############################################################################
        # 資料傳輸
        que_updateFrame = multiprocessing.Queue()
        self.parent_fullFrame, child_fullFrame = multiprocessing.Pipe(duplex=True)

        ####################################################################################################
        # 設定process

        self.process_list = list()

        # Camera Process
        for camId, camData in enumerate(self.cameraDatas):
            p = multiprocessing.Process(target=readCam, args=[camData, camId, que_updateFrame])
            p.name = f'{camData}'
            self.process_list.append(p)

        
        # Concat Process
        p = multiprocessing.Process(target=concatFrame, args=[self.cameraDatas, self.cameraCnt, que_updateFrame, child_fullFrame])
        self.process_list.append(p)

        ####################################################################################################
        # 開始執行
        p: multiprocessing.Process
        for p in self.process_list:
            p.start()
        
        self.starting = True

    def read(self):
        try:
            self.parent_fullFrame.send(1)
            res = self.parent_fullFrame.recv() # block
        except:
            return False, None
        
        return True, res


    def close(self):
        if not self.starting:
            return

        # 設定等待結束
        p: multiprocessing.Process
        for p in self.process_list:
            p.terminate()
            p.join()
        self.starting = False

    
def readCam(info, id: int, q: multiprocessing.Queue):
    cap = cv2.VideoCapture(info['url']['rtsp'])
    while True:
        ret, frame = cap.read()

        if ret:
            #frame = rotate(frame, 90)
            q.put({
                'id': id,
                'data': frame
            })
            time.sleep(0.02)


def concatFrame(info,camCount:int, que_frame: multiprocessing.Queue, conn_fullImage:Connection):
    images = [np.zeros([480, 640, 3], dtype=np.uint8) for _ in range(camCount)]
    while True:
        if not que_frame.empty():
            res = que_frame.get()

            camId = res['id']
            data = res['data']
            
            images[camId] = data   

            if info[camId]['rotate'] != 0:
                images[camId] = r(images[camId],info[camId]['rotate'])  
      
        
        if conn_fullImage.poll():
            conn_fullImage.recv()

            #####

            cat_image = concatImage(images)




            #####
            conn_fullImage.send(cat_image)

def concatImage(images):
    


    return cv2.hconcat(images)


def r(image, angle):
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1)
    rotated_padded = cv2.warpAffine(image, M, (w, h))
    
    return  rotated_padded
    