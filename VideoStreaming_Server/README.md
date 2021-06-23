# 影像傳遞伺服器
將多台ESP32 CAM的影像透過網路傳遞，並整合成單一影像後提供串流服務

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
2. 啟動伺服器\
   `python server.py`
3. 連接`http://<ip>/stream`即可取得http stram影像
4. 若無人連接會自動斷開伺服器與攝影機的連線以省電，有人使用後則會恢復
5. 若使用rtsp協定版本在伺服器與攝影機斷開後再次啟動會黑畫面一旦時間，以為攝影機正在啟動rtsp伺服器的緣故
6. 目前版本的 `server.py` 可提供多人同時連線

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

- 測試讀取與拼接
    - `rawVideo_record.py`\
        擷取相機影像並直接串接輸出成檔案

    - `rawVideo_concat.py`\
        讀取直接串接的影像，拆解回各相機影像後再進行投影及裁切

- 影像伺服器
    - `server.py`\
        該檔案為開啟伺服器之主程式\
        **開啟方法** `python server.py`

