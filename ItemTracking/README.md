# 物件追蹤伺服器

由 http 取得影像後，對輸送帶上方的物件進行追蹤

## 環境安裝

使用 `pipenv` 套件架設

1. 安裝 pipenv\
   `pip install pipenv`
2. 安裝相關套件\
   `pipenv install`

## 使用說明

1. 更改 `data/location.json` 中輸送帶和實際座標的對應表格
   - 格式如下
     ```json
     {
       "locationPoint": [
         [0, 2570],
         [50, 2138],
         [100, 1706],
         [150, 1346],
         [200, 993],
         [250, 635],
         [300, 219],
         [350, -197]
       ]
     }
     ```
   - `locationPoint` 中的每一列為 `[實際座標, pixel]`
2. 更改 `data/connect_config.json` 中**mqtt**和**httpUrl**
   - 格式如下
     ```json
     {
       "mqtt": {
         "ip": "127.0.0.1",
         "port": 1883
       },
       "http url": "http://192.168.1.1/stream"
     }
     ```
3. 執行 `python main.py` 即可啟動

## 程式說明

- MQTT Client\
  負責處理 mqtt 的 publish 和 subsrcibe

  ````python
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

  ````

- http request\
  持續擷取**影像傳遞伺服器**輸出的影像

  ````python
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

  ````

- 物件定位

  ```python
  def track(que_frame: multiprocessing.Queue, que_Id: multiprocessing.Queue, que_publish: multiprocessing.Queue):
      ...
      while True:
          ...
          if not que_frame.empty():
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
                contours, hierarchy = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
  ```

- 物體追蹤\
  `functions.py` / `git_index()` 1. 輸入參數格數\
   `pre_result` ： `[[location, x, y, w, h], ...]`\
   `new_xs` ： `[[location, x, y, w, h], ...]` 2. 設定最小閥值
  `python # 距離20cm內視為同物體的移動 THRESHOLD = 20 ` 3. 判斷是否為第一個物體\
   - **是** 則直接新增
  `python for loc, *box in new_xs: # 物體在50cm(定義的開始位置)內才會新增 if loc < 50: result = np.concatenate((result, np.expand_dims([loc, *box], axis=0)), axis=0) `

          - **否** 則考慮追蹤
          ```python
          for loc, *box in new_xs:
                  # 計算直線距離
                  dis = [get_distance(loc, pre) for pre, *_ in pre_result]
                  # 尋找最小距離
                  min_index = np.argmin(dis)

                  if dis[min_index] < THRESHOLD:
                      # 發現新舊物體框之間的距離小於閥值，將更新最近的物體框
                      result[min_index, :] = loc, *box
                  else:
                      # 新物體框附近未有已存在的物體框，因此當作是新的物體進入追蹤範圍
                      # 物體在50cm(定義的開始位置)內才會新增
                      if loc < 50:
                          result = np.concatenate((result, np.expand_dims([loc, *box], axis=0)), axis=0)
          ```

- 座標轉換\
  `functions.py` / `getlocation()` 1. 由 `/data/location.json` 讀取位置參數
  `python locationPoints = json.load(open('./data/location.json', mode='r'))['locationPoint'] ` 1. 判斷目標是否超出追蹤範圍
  `python if x_pixel > locationPoints[0][1]: return -1 if x_pixel < locationPoints[-1][1]: return -1 ` 1. 由檔案中尋找最近的標點
  ```python
  upperIndex, lowerIndex = -1, -1
  for n in range(len(locationPoints)):
  if locationPoints[n][1] == x_pixel:
  return locationPoints[n][0]

          if locationPoints[n][1] > x_pixel:
              upperIndex = n

          if locationPoints[n][1] < x_pixel:
              lowerIndex = n
              break
      upperReal, upperPixel = locationPoints[upperIndex]
      lowerReal, lowerPixel = locationPoints[lowerIndex]
      ```
      1. 使用內插法計算估計位置
      ```python
      result = lowerReal + (x_pixel - lowerPixel)/(upperPixel - lowerPixel) * (upperReal - lowerReal)
      ```

## 方法

### 座標轉換

![](/ItemTracking/img/輸送帶位置.jpg)
先在輸送帶上測量幾個座標點的位置，在利用內插法計算出物體目前的位置

### 目標追蹤

為了避免目標在影格遺失的狀況造成物體順序錯誤，我們設定讓目標框只在特定範圍內更新，若距離太遠則當作是不同物體，即會給定新的 index 給該目標框
![](/ItemTracking/img/追蹤示意圖.jpg)
而在物體中途被取走逕行加工的部份，我們可以透過調整該物體框的位置，讓該物體在回到輸送帶時也能夠正確的繼續追蹤
