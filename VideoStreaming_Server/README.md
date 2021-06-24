# 影像傳遞伺服器

單一 ESP32-CAM 一次只能負擔一個連線，為了能讓所有服務都可以取得影像，因此另架設一台伺服器收集並處理影像，再透過 http 提供所有使用者影像串流服務

## 環境安裝

- 使用 `pipenv` 套件架設
- 執行 `pipenv install` 可安裝相關套件

## 使用說明

1. 更改 `/config/cameras_config.json`
   - 內容格式為
   ```json
   {
     "camera": [
       {
         "url": {
           "jpg": "<可取得單張jpg影像的網址>",
           "rtsp": "<rtsp網址>"
         },
         "rotate": 0,
         "perspective": {
           "src": [
             [0, 92],
             [0, 325],
             [640, 349],
             [640, 116]
           ],
           "width": 680,
           "hight": 250
         },
         "concat_x": {
           "front": 0,
           "back": 632
         }
       }
     ]
   }
   ```
   - 有幾台攝影機就需在`camera`內重複幾次
   - `rotate`代表取得影像後需翻轉的角度，目前只支援**0**或**180**
   - `perspective`
     - `src` 代表原始影像需進行投影變換的四邊形的 4 個角
     - `width` 為變換後影像寬度
     - `hight` 為變換後影像高度
   - `concat_x`
     - `front` 代表與前一張照片拼接時使用的 x 方向 pixel 位置(**無則填 0 即可**)
     - `back` 代表與後一張照片拼接時使用的 x 方向 pixel 位置(**無則填該張照片寬度即可**)
2. 更改 `server.py` 檔案引用的模組
   - 若要使用 rtsp 作為連接攝影機的方式
   ```python
   from Camera import rtsp_cam as Cam
   ```
   - 若要使用單張擷取 jpg 圖片作為連接攝影機的方式
   ```python
   from Camera import jpg_cam as Cam
   ```
3. 啟動伺服器\
   `python server.py`\
   會輸出這些內容代表成功啟動
   ![server output](/VideoStreaming_Server/img/server輸出.jpg)
4. 對 `http://<ip>:5000/stream` 發出 GET request 即可取得 http stram 影像\
   會拿到如下圖已拼接後的影像
   ![concat_image](/VideoStreaming_Server/img/rawframe_concat.jpg)
5. http stream 讀取範例如下,一般會將它放在另一 thread 中執行,並將影像傳輸回主程式處理

   ```python
   url = 'http://127.0.0.1:5000/stream'
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
               frame = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)

               # frame 即為單張影像
   else:
       print("Received unexpected status code {}".format(r.status_code))
   ```

6. 若無人連接會自動斷開伺服器與攝影機的連線以省電，有人使用後則會恢復
7. 若使用 rtsp 協定版本在伺服器與攝影機斷開後再次啟動會黑畫面一段時間，以因為攝影機正在啟動 rtsp 伺服器的緣故
8. 目前版本的 `server.py` 可提供多人同時連線

## 檔案說明

- 相機連線\
  `Camera.py`

  - 結構

    ```python
    class CameraName():
        def __init__(self):
            # 初始宣告，讀取檔案
            ...

        def start(self):
            # 啟動各相機擷取程序與相片串接程序
            ...

        def read(self):
            # 擷取影像
            ...

        def close(self):
            # 關閉所有程序
            ...

        def process_readCam(info, id: int, q: multiprocessing.Queue):
            # 讀取影像用程序
            ...

        def process_concatFrame(info, camCount:int, que_frame: multiprocessing.Queue, conn_fullImage:Connection):
            # 拼接用程序
            ...
    ```

  - 使用範例

    ```python
    from Camera import jpg_cam as Cam

    cap = Cam()
    cap.start()
    while True:
        ret, frame = cap.read()
        # frame 為當次影格
        # ret 代表是否成功,False代表沒有影格可輸出
        if not ret:
            continue

        # ----------------
        # 要做的處理
        # ----------------
    cap.close()
    ```

- 測試讀取與拼接

  - `testing_code/rawVideo_record.py`\
     擷取相機影像並直接串接輸出成檔案

  - `testing_code/rawVideo_concat.py`\
     讀取直接串接的影像，拆解回各相機影像後再進行投影及裁切

- 影像伺服器

  - `server.py`\
     該檔案為開啟伺服器之主程式

    - 使用 Flask 實作
    - 功能介紹

      - 休眠\
        每次有連線讀取影格時，會更新最後讀取時間，並計算是否閒置
        若閒置超過 30 秒則會關閉傳遞伺服器與攝影機的網路連線

        ```python
        def gen_frames():
            ...
            while True:
              # 更新時間
                readTime = time.time()
                ...

        def updateFrame():
          ...
          while True:

            ...
            # 若最後連線時間小於30秒則關閉，反之則開啟
            if (time.time() - readTime > 30) and (cap.starting == True): # sec
              print('close')
              cap.close()
              time.sleep(1)
            elif (time.time() - readTime < 30) and (cap.starting == False):
                print('start')
                cap.start()

            ...
        ```

      - 多人讀取攝影機\
        透過預先將設影機畫面儲存在伺服器端，每一連線不需要重新從攝影機端提取影格，而是直接取用伺服器端所儲存的資料\
        **伺服器的影格更新會在有人連線時不斷更新，以確保即時性**

        ```python
        def gen_frames():
            ...
            while True:
                ...
                if now_frame is None:
                    break
                # 讀取影格並發送
                ret, buffer = cv2.imencode('.jpg', now_frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

        def updateFrame():
          ...
          while True:
            ...
            if cap.starting:
              ...
              # 將新影格存入伺服器端記憶體
              now_frame = frame

        ```

      - 影像合併

        - 合併結果圖
          ![](/img/拼接.gif)
        - 做法

        ```python
        def concatImage(images):
            global info
            # 根據config檔案中設定的邊界，對圖片投影變換
            for n, img in enumerate(images):
                src_contour = info[n]['perspective']['src']
                width = info[n]['perspective']['width']
                hight = info[n]['perspective']['hight']

                pts1 = np.float32(src_contour)
                pts2 = np.float32([(0, 0), (0, hight), (width, hight), (width, 0)])
                M = cv2.getPerspectiveTransform(pts1, pts2)
                dst = cv2.warpPerspective(img, M, (width, hight))
                images[n] = dst

            # 將圖片按照設定的位置水平拼接，組成完成圖
            for n, img in enumerate(images):
                front = info[n]['concat_x']['front']
                back = info[n]['concat_x']['back']

                images[n] = img[:, front:back, :]

            return cv2.hconcat(images)
        ```

    -
