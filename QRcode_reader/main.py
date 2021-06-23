# 匯入所需工具包
from imutils.video import VideoStream
from pyzbar import pyzbar
import argparse
import datetime
import imutils
import time
import cv2
import paho.mqtt.client as mqtt
import random
import json  
import csv
from apscheduler.schedulers.background import BackgroundScheduler
# 建立引數解析器，解析引數
ap = argparse.ArgumentParser()
ap.add_argument("-o", "--output", type=str, default="barcodes.csv",
 help="path to output CSV file containing barcodes")
args = vars(ap.parse_args())

_g_cst_ToMQTTTopicServerIP = "140.116.155.190"
_g_cst_ToMQTTTopicServerPort = 1883
_g_cst_MQTTTopicName = "Label"
mqttc = mqtt.Client("python_pub")
mqttc.connect(_g_cst_ToMQTTTopicServerIP, _g_cst_ToMQTTTopicServerPort)

# 初始化視訊
print("[INFO] starting video stream...")
vs = VideoStream(src=1).start()
#vs = VideoStream(usePiCamera=True).start() 樹梅派
time.sleep(2.0)

# 開啟輸出CSV檔案，用來寫入和初始化迄今發現的所有條形碼
csv = open(args["output"], "w")
found = set()


#副程序當主程序讀到barcode值會每5秒寫入資料夾的barcodes.csv
sched = BackgroundScheduler(daemon=True)
barcodeData="start"
#found.add(barcodeData)
def my_job():
    if barcodeData not in found :
       csv.write("{},{}\n".format(datetime.datetime.now(),barcodeData))
       csv.flush()
       found.add(barcodeData) 
       print (json.dumps(barcodeData))
       mqttc.publish(_g_cst_MQTTTopicName, json.dumps(barcodeData))
sched.add_job(lambda : my_job(),'interval',seconds=1)
sched.start()

# 迴圈來自視訊流的幀
while True:
 # 抓取來自單執行緒視訊流的幀， 
 # 將大小重新調整為最大寬度400畫素
 frame = vs.read()
 frame = imutils.resize(frame, width=600)

 # 找到視訊中的條形碼，並解析所有條形碼
 barcodes = pyzbar.decode(frame)
  # 迴圈檢測到的條形碼
 for barcode in barcodes:
  # 提取條形碼的邊界框位置
  # 繪出圍繞影象上條形碼的邊界框
  (x, y, w, h) = barcode.rect
  cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

  # 條形碼資料為位元組物件，所以如果我們想把它畫出來
  # 需要先把它轉換成字串
  barcodeData = barcode.data.decode("utf-8")
  barcodeType = barcode.type

  # 繪出影象上的條形碼資料和型別
  text = "{} ({})".format(barcodeData, barcodeType)
  cv2.putText(frame, text, (x, y - 10),
  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

# 展示輸出幀
 cv2.imshow("Barcode Scanner", frame)
 key = cv2.waitKey(1) & 0xFF

  # 如果按下”q”鍵就停止迴圈
 if key == ord("q"):
  break

# 關閉輸出CSV檔案進行清除
print("[INFO] cleaning up...")
csv.close()
cv2.destroyAllWindows()
vs.stop()


