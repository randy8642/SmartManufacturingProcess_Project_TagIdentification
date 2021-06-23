import json
import multiprocessing
from multiprocessing.connection import Connection
import cv2
import numpy as np
import time
import requests


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
        # que_updateFrame = multiprocessing.Queue()
        self.parent_fullFrame, child_fullFrame = multiprocessing.Pipe(duplex=True)
        self.parent_cam_pipes, self.child_cam_pipes = list(), list()
        for camId, camData in enumerate(self.cameraDatas):
            parent, child = multiprocessing.Pipe(duplex=True)
            self.parent_cam_pipes.append(parent)
            self.child_cam_pipes.append(child)

        ###############################################################################
        # 設定process

        self.process_list = list()

        # Camera Process
        for camId, camData in enumerate(self.cameraDatas):
            p = multiprocessing.Process(target=process_readCam, args=[
                                        camData, camId,  self.child_cam_pipes[camId]])
            p.name = f'{camData}'
            self.process_list.append(p)

        # Concat Process
        p = multiprocessing.Process(target=process_concatFrame, args=[self.cameraDatas,
                                    self.cameraCnt,  child_fullFrame, self.parent_cam_pipes])
        self.process_list.append(p)

        ####################################################################################################
        # 開始執行
        p: multiprocessing.Process
        for p in self.process_list:
            p.start()

        self.starting = True

    def read(self):
        # 讀取影格
        try:
            self.parent_fullFrame.send(1)
            res = self.parent_fullFrame.recv()  # block
        except:
            return False, None

        return True, res

    def close(self):
        # 關閉所有副程序
        if not self.starting:
            return

        # 設定等待結束
        p: multiprocessing.Process
        for p in self.process_list:
            p.terminate()
            p.join()
        self.starting = False

# 相機讀取程序
def process_readCam(info: str, id: int, conn: Connection):

    while True:
        if conn.poll():
            conn.recv()

            #####

            url = info['url']['jpg']
            resp = requests.get(url, stream=True).raw
            image = np.asarray(bytearray(resp.read()), dtype="uint8")
            image = cv2.imdecode(image, cv2.IMREAD_COLOR)

            #####
            conn.send(image)

        time.sleep(0.01)

# 影像拼接程序
def process_concatFrame(info,camCount: int, conn_fullImage: Connection, conns):
    images = [np.zeros([480, 640, 3], dtype=np.uint8) for _ in range(camCount)]
    while True:

        
        # 當收到取得圖像的要求時執行
        if conn_fullImage.poll():
            conn_fullImage.recv()
            # 向各相機要求擷取圖片
            for conn in conns:
                conn: Connection
                conn.send(1)

            # 讀取各相機擷取的圖片
            for camId, conn in enumerate(conns):
                conn: Connection
                if conn.poll(timeout=0.01):
                    images[camId] = conn.recv()  # block

                    # 根據config檔對鏡頭圖片翻轉
                    if info[camId]['rotate'] != 0:
                        images[camId] = r(images[camId],info[camId]['rotate'])  

            # 串接圖像
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

def rotate(image, angle,  scale=1.0):

    (h, w) = image.shape[:2]

    padding = (w - h) // 2
    center = (w // 2, w // 2)

    img_padded = np.zeros(shape=(w, w, 3), dtype=np.uint8)
    img_padded[padding:padding+h, :, :] = image

    M = cv2.getRotationMatrix2D(center, angle, scale)
    rotated_padded = cv2.warpAffine(img_padded, M, (w, w))

    rotated = rotated_padded[:, padding:padding+h, :]

    return rotated
