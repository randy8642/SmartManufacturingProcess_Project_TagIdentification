# -*- coding: utf-8 -*-

import numpy as np
import cv2
from functions import getlocation, get_index

cap = cv2.VideoCapture('./src/output_concat_Trim.mp4')
# out = cv2.VideoWriter('output_located.mp4', cv2.VideoWriter_fourcc(*'mp4v'), 24, (2347, 250))

id_list = ['123', '456', '789']

pre_img = None
pre_boxs = np.empty([0, 5])
while(True):

    # Capture frame-by-frame
    ret, frame = cap.read()

    if not ret:
        break

    next_img = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    next_img = cv2.GaussianBlur(next_img, (3, 3), 0)

    if pre_img is None:
        pre_img = next_img
        continue


    vis = cv2.absdiff(next_img, pre_img)
    cv2.imshow('',cv2.resize(vis,(1500,200)))
    cv2.waitKey(1)
    #pre_img = next_img

    ret, th = cv2.threshold(vis, 50, 255, cv2.THRESH_BINARY)
    dilated = cv2.dilate(th, None, iterations=1)
    contours, hierarchy = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes = []
    for n_contour, contour in enumerate(contours):        

        x, y, w, h = cv2.boundingRect(contour)  # 該最大contour的(x,y)位置及長寬
        if w < 60:
            continue

        location = round(getlocation(x - w/2), ndigits=1)
        
        boxes.append([location, x, y, w, h])
    
    full_boxs = get_index(pre_boxs, boxes)

    if full_boxs.shape[0] > 0 and full_boxs[0, 0] > 330:
        # END - pop box
        full_boxs = np.delete(full_boxs, 0, 0)
        id_list.pop(0)
        
        
        
    
    for n, (loc, x, y, w, h) in enumerate(full_boxs):
        
        x, y, w, h = int(x), int(y), int(w), int(h)
        #cv2.drawContours(frame, contour, -1, (0, 255, 0), 2)
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(frame, f'loc {loc}cm', (x, y-5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        cv2.putText(frame, f'index', (x+30, y+30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
        cv2.putText(frame, f'{n+1}', (x+30, y+70), cv2.FONT_HERSHEY_SIMPLEX, 1.7, (0, 0, 255), 2)
        # cv2.putText(frame, f'ID', (x+30, y+30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
        # cv2.putText(frame, f'{id_list[n]}', (x+30, y+70), cv2.FONT_HERSHEY_SIMPLEX, 1.7, (255, 0, 0), 2)

    pre_boxs = full_boxs
    #out.write(frame)
    frame = cv2.resize(frame, (1500, 200))
    cv2.imshow('frame', frame)
    cv2.waitKey(1)


#out.release()
cap.release()
cv2.destroyAllWindows()
