# 物件追蹤伺服器
由http取得影像後，對輸送帶上方的物件進行追蹤

## 環境安裝
- 使用 `pipenv` 套件架設
- 執行 `pipenv install` 可安裝相關套件


## 使用說明
1. 更改 `location.json` 中輸送帶和實際座標的對應表格
   - 格式如下
        ```json
        {
            "locationPoint": [
                [ 0, 2570 ],        
                [ 50, 2138 ],
                [ 100, 1706 ],
                [ 150, 1346 ],
                [ 200, 993 ],
                [ 250, 635 ],
                [ 300, 219 ],
                [ 350, -197 ]
            ]
        }
        ```
    - `locationPoint` 中的每一列為 `[實際座標, pixel]`
2. 更改**mqtt ip 以及 port**\
   在 `main.py` 中 `mqtt_client` 函式內
   ```python
   client.connect(ip, port, 60)
   ```
   
3. 執行 `python main.py` 即可啟動

## 程式說明
1. 啟動
程式啟動時即會開啟3個程序，分別用作
    - MQTT Client\
    負責處理mqtt的publish和subsrcibe
        ```python
        def mqtt_client(que_id: multiprocessing.Queue, que_publish: multiprocessing.Queue):
            def on_connect(client, userdata, flags, rc):
                print("Connected with result code " + str(rc))

                client.subscribe("Label")

            def on_message(client, userdata, msg):
                # 轉換編碼utf-8
                id_msg = msg.payload.decode('utf-8')
                que_id.put(id_msg)

            client = mqtt.Client()
            client.on_connect = on_connect
            client.on_message = on_message
            client.username_pw_set("<username>", "<password>")
            client.connect(ip, port, 60)

            
            while True:
                # 從broker接收訊息
                client.loop()

                # 當有需要publish時執行
                if not que_publish.empty():
                    res = que_publish.get()
                    topic = res['topic']
                    msg = res['msg']

                    client.publish(topic, payload=msg, qos=0)
        ```
    - http request\
    持續擷取**影像傳遞伺服器**輸出的影像
        ```python
        def get_frame(que: multiprocessing.Queue):

            url = 'http://<ip>/stream'

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

                            # 將影格(frame)傳遞給處理程序
                            que.put(frame)    
                else:
                    print(f"Received unexpected status code {r.status_code}")

        ```
    - 影像處理\
        處理物體定位及追蹤
        ```python
        ...
        # 將圖片轉為灰階
        next_img = cv2.cvtColor(res_frame, cv2.COLOR_BGR2GRAY)
        ...
        # 計算當前圖片與第一張圖片的差異
        vis = cv2.absdiff(next_img, pre_img)

        # 設定閥值
        ret, th = cv2.threshold(vis, 50, 255, cv2.THRESH_BINARY)
        # 邊緣膨脹(讓目標檢測更容易)
        dilated = cv2.dilate(th, None, iterations=1)
        # 尋找物體框
        contours, hierarchy = cv2.findContours(
            dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        ```
2. 


## 方法
### 座標轉換
![輸送帶位置](/img/輸送帶位置.jpg)
先在輸送帶上測量幾個座標點的位置，在利用內插法計算出物體目前的位置

### 目標追蹤
為了避免目標在影格遺失的狀況造成物體順序錯誤，我們設定讓目標框只在特定範圍內更新，若距離太遠則當作是不同物體，即會給定新的index給該目標框
![](/img/追蹤示意圖.jpg)
而在物體中途被取走逕行加工的部份，我們可以透過調整該物體框的位置，讓該物體在回到輸送帶時也能夠正確的繼續追蹤