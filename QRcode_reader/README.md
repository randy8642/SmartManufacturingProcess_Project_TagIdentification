# QRcode Reader

## 說明

使用 usb 攝影機對工件上的 QRcode 進行讀取，並透過 mqtt 傳遞給需要的系統

## 環境安裝

- 使用 `pipenv` 套件架設
- 執行 `pipenv install` 可安裝相關套件

## 使用說明

1. 街上 USB 攝影機並安裝驅動程式
2. 開啟 cmd 並輸入 `python main.py --output barcodes.csv`


## 檔案說明

- mqtt

  - 設定\
    設定 mqtt broker 的 IP 位置以及用於連線的 port 號

  ```python
  _g_cst_ToMQTTTopicServerIP = "127.0.0.1"
  _g_cst_ToMQTTTopicServerPort = 1883
  mqttc = mqtt.Client("python_pub")
  mqttc.connect(_g_cst_ToMQTTTopicServerIP, _g_cst_ToMQTTTopicServerPort)
  ```

  - publish\
    使用 scheduler 工具，設定每 1 秒判斷一次是否有新的工件編號需要發送\
    **當讀到新的barcode值會寫入資料夾的暫存barcodes.csv及MQTT發送到出去**

  ```python
   _g_cst_MQTTTopicName = "Label"

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
  ```
  - 展示\
  ![qrcode_mqtt](/QRcode_reader/img/qrcode_mqtt.gif)

- qrcode讀取  
  - 作法
  ```python
  while True:
    ...

    # 找到視訊中的條碼，並解析條碼
    barcodes = pyzbar.decode(frame)

    # 迴圈檢測到的條形碼
    for barcode in barcodes:
      ...
      # 讀取影象上的條碼的解碼結果和條碼類別
      barcodeData = barcode.data.decode("utf-8")
      barcodeType = barcode.type
      ...
  ```
  - 結果圖\
  ![qrcode_detect](/QRcode_reader/img/qrcode_detect.gif)
