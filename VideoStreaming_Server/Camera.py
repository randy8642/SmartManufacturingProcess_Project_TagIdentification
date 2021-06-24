import json
import multiprocessing
from multiprocessing.connection import Connection
import cv2
import numpy as np
import time
import requests

# RTSP
class rtsp_cam():
    def __init__(self) -> None:

        self.cameraDatas = json.load(open('./config/cameras_config.json'))['camera']
        self.cameraCnt = len(self.cameraDatas)
        
        self.starting = False

        # 設定process
        self.process_list = list()
      
    
    
    def start(self):
        if self.starting:
            return
            
        ###############################################################################
        # 資料傳輸
        que_updateFrame = multiprocessing.Queue()
        self.parent_fullFrame, child_fullFrame = multiprocessing.Pipe(duplex=True)

        ####################################################################################################
        

        # Camera Process
        for camId, camData in enumerate(self.cameraDatas):
            p = multiprocessing.Process(target=self.process_readCam, args=[camData, camId, que_updateFrame])
            p.name = f'{camData}'
            self.process_list.append(p)

        # Concat Process
        p = multiprocessing.Process(target=self.process_concatFrame, args=[self.cameraDatas, self.cameraCnt, que_updateFrame, child_fullFrame])
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

    
    def process_readCam(info, id: int, q: multiprocessing.Queue):
        # 使用openCV函式與rtsp伺服器通訊
        cap = cv2.VideoCapture(info['url']['rtsp'])
        while True:
            # 讀取1個影格
            ret, frame = cap.read()

            # 若成功讀取就把該影格透過Queue傳遞給合併影格的程序
            if ret:           
                q.put({
                    'id': id,
                    'data': frame
                })

                # 最少間隔0.02s
                time.sleep(0.02)


    def process_concatFrame(info,camCount:int, que_frame: multiprocessing.Queue, conn_fullImage:Connection):
        images = []
        while True:
            # 持續接收攝影機玩來的影像並儲存
            if not que_frame.empty():
                res = que_frame.get()

                camId = res['id']
                data = res['data']

                if len(images) == 0:
                    images = [np.zeros_like(data, dtype=np.uint8) for _ in range(camCount)]
                
                images[camId] = data   

                if info[camId]['rotate'] != 0:
                    images[camId] = rotate(images[camId], info[camId]['rotate'])  
        
            # 若有影像請求，則會將影像合併並發送
            if conn_fullImage.poll():
                conn_fullImage.recv()

                # 水平串接
                cat_image = cv2.hconcat(images)

                # 發送
                conn_fullImage.send(cat_image)

# JPG
class jpg_cam():
    def __init__(self) -> None:

        self.cameraDatas = json.load(
            open('./config/cameras_config.json'))['camera']
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
        self.parent_fullFrame, child_fullFrame = multiprocessing.Pipe(
            duplex=True)
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
            p = multiprocessing.Process(target=self.process_readCam, args=[
                                        camData, camId,  self.child_cam_pipes[camId]])
            p.name = f'{camData}'
            self.process_list.append(p)

        # Concat Process
        p = multiprocessing.Process(target=self.process_concatFrame, args=[self.cameraDatas,
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
    def process_concatFrame(info, camCount: int, conn_fullImage: Connection, conns):
        images = [np.zeros([480, 640, 3], dtype=np.uint8)
                  for _ in range(camCount)]
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
                            images[camId] = rotate(
                                images[camId], info[camId]['rotate'])

                # 串接圖像
                cat_image = cv2.hconcat(images)

                #####
                conn_fullImage.send(cat_image)

# functions
def rotate(image, angle):
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1)
    rotated_padded = cv2.warpAffine(image, M, (w, h))
    
    return  rotated_padded
    