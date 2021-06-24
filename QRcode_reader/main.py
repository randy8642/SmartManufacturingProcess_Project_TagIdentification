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

# 設定MQTT傳輸的IP、port及Topic，並連線
_g_cst_ToMQTTTopicServerIP = "127.0.0.1"
_g_cst_ToMQTTTopicServerPort = 1883
_g_cst_MQTTTopicName = "Label"
mqttc = mqtt.Client("python_pub")
mqttc.connect(_g_cst_ToMQTTTopicServerIP, _g_cst_ToMQTTTopicServerPort)

# 初始化視訊
print("[INFO] starting video stream...")
vs = VideoStream(src=0).start()
# vs = VideoStream(usePiCamera=True).start() 樹梅派
time.sleep(2.0)

# 開啟輸出CSV檔案，用來寫入掃描到的條碼
csv = open(args["output"], "w")
found = set()


# 當讀到新的barcode值會寫入資料夾的暫存barcodes.csv及MQTT發送到出去
sched = BackgroundScheduler(daemon=True)
# 設定起始barcode值
barcodeData = "start"


def my_job():
    if barcodeData not in found:
        csv.write("{},{}\n".format(datetime.datetime.now(), barcodeData))
        csv.flush()
        found.add(barcodeData)
        print(json.dumps(barcodeData))
        mqttc.publish(_g_cst_MQTTTopicName, json.dumps(barcodeData))


sched.add_job(lambda: my_job(), 'interval', seconds=1)
sched.start()

# 迴圈來自視訊流的幀
while True:
    # 抓取來自單執行緒視訊流的幀，
    # 將大小調整為最大寬度600畫素
    frame = vs.read()
    frame = imutils.resize(frame, width=600)

    # 找到視訊中的條碼，並解析條碼
    barcodes = pyzbar.decode(frame)
    # 迴圈檢測到的條形碼
    for barcode in barcodes:
     # 提取條碼的邊界框位置
     # 繪出條碼的邊界框
        (x, y, w, h) = barcode.rect
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

        # 繪出影象上的條碼的解碼結果和條碼類別
        barcodeData = barcode.data.decode("utf-8")
        barcodeType = barcode.type
        text = "{} ({})".format(barcodeData, barcodeType)
        cv2.putText(frame, text, (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

# 展示輸出幀
    cv2.imshow("Barcode Scanner", frame)
    key = cv2.waitKey(1) & 0xFF

    # 如果按下”q”鍵就停止迴圈
    if key == ord("q"):
        break

# 關閉輸出後刪除暫存的CSV檔案
print("[INFO] cleaning up...")
csv.close()
cv2.destroyAllWindows()
vs.stop()
