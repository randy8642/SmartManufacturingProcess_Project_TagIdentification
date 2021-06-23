# 影像傳遞伺服器
單一ESP32-CAM一次只能負擔一個連線，為了能讓所有服務都可以取得影像，因此另架設一台伺服器收集並處理影像，再透過http提供所有使用者影像串流服務

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
                        [0,92],
                        [0,325],
                        [640,349],
                        [640,116]
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
     - `src` 代表原始影像需進行投影變換的四邊形的4個角
     - `width` 為變換後影像寬度
     - `hight` 為變換後影像高度
   - `concat_x`
     - `front` 代表與前一張照片拼接時使用的x方向pixel位置(**無則填0即可**)
     - `back` 代表與後一張照片拼接時使用的x方向pixel位置(**無則填該張照片寬度即可**)
2. 更改 `server.py` 檔案引用的模組
    - 若要使用rtsp作為連接攝影機的方式
    ```python
    from cam_rtsp import Camera
    ```
    - 若要使用單張擷取jpg圖片作為連接攝影機的方式    
    ```python
    from cam_jpg import Camera
    ```
    
3. 啟動伺服器\
   `python server.py`\
   會輸出這些內容代表成功啟動
   ![server output](/VideoStreaming_Server/img/server輸出.jpg)
4. 對 `http://<ip>:5000/stream` 發出GET request即可取得http stram影像\
會拿到如下圖已拼接後的影像
![concat_image](/VideoStreaming_Server/img/rawframe_concat.jpg)
5. http stream 讀取範例如下,一般會將它放在另一thread中執行,並將影像傳輸回主程式處理
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
7. 若使用rtsp協定版本在伺服器與攝影機斷開後再次啟動會黑畫面一段時間，以因為攝影機正在啟動rtsp伺服器的緣故
8. 目前版本的 `server.py` 可提供多人同時連線

## 檔案說明
- 相機連線  
    在收到圖片取用需求時才會連線相機並取得影像
    - `cam_rtsp.py`\
        使用rtsp作為連線相機的方法\
        函數內部定義如下
        ```python
        class Camera():
            def __init__(self) -> None:
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
        ```
        影像擷取使用openCV內建函式
        ```python
        cap = cv2.VideoCapture('<rtsp 網址>')
        ```

    - `cam_jpg.py`\
        以每次單張jpg影像的方式擷取\
        同上，只有在影像擷取處更改為
        ```python
        url = '<jpg 網址>'
        resp = requests.get(url, stream=True).raw
        image = np.asarray(bytearray(resp.read()), dtype="uint8")
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        ```
    - 若要單獨使用 `cam_jpg` 以及 `cam_rtsp` ,可參照以下用法使用
        ```python
        from cam_jpg import Camera

        cap = Camera()
        cap.start()
        while True:
            ret, frame = cap.read()
            # frame 為當次影格
            # ret 代表是否成功,False代表沒有影格可輸出

            if not ret:
                continue

            # 以下放要做的處理
        cap.close()
        ```

- 測試讀取與拼接
    - `rawVideo_record.py`\
        擷取相機影像並直接串接輸出成檔案

    - `rawVideo_concat.py`\
        讀取直接串接的影像，拆解回各相機影像後再進行投影及裁切

- 影像伺服器
    - `server.py`\
        該檔案為開啟伺服器之主程式
        
        
        

