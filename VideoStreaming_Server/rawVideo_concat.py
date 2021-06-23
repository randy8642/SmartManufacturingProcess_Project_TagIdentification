'''
https://docs.opencv.org/master/da/d6e/tutorial_py_geometric_transformations.html
'''

import cv2
from matplotlib import image
import numpy as np
import matplotlib.pyplot as plt
import json


info = ''

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


def main():
    # READ
    json_data = json.load(open('./cameras_jpg.json', 'r'))
    global info
    info = json_data['camera']
    location = json_data['locationPoint']
    del json_data

    # 
    cap = cv2.VideoCapture('./test_v5_rtsp/output.mp4')
    camCount = 4
    images = [np.zeros([480, 640, 3], dtype=np.uint8) for _ in range(camCount)]
    
    out = cv2.VideoWriter('output_concat.mp4', cv2.VideoWriter_fourcc(*'mp4v'), 24, (2347, 250))

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        ###################################################
        # 拆解傳輸過來的圖片，回到各相機分開的狀態
        for n in range(camCount):
            images[n] = frame[:, n * 640:(n + 1) * 640, :]

        ###################################################
        # 串接及投影處理
        cat_image = concatImage(images)

        # 輸出影格
        out.write(cat_image)
        
    out.release()

if __name__ == '__main__':
    main()
