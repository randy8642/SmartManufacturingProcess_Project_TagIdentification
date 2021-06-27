# UI介面設計

## 說明
使用 QT Designer 等相關 UI 設計之軟體，把所需的的介面輪廓設計出來，再把每
個 Button、Label、Text 之作用，套入所需之程式碼

## 環境安裝
- python 版本 `3.9.2`
- 使用 `pipenv` 套件架設
    1. 安裝pipenv\
    `pip install pipenv`
    2. 安裝相關套件\
    `pipenv install`

## 使用說明
1. 打開 QT Designer 設計所需介面，設計完即可存成 ui 檔
2. 開啟 cmd 並輸入 `pyuic5 -x finalproject.ui -o finalproject.py`
3. 利用程式編譯器打開 `*.py` 檔，即可編輯程式碼

## 程式說明
- Button
    - Connect the button to the function
        ```python
        self.cam1btn.clicked.connect(self.cam1)
        self.cam2btn.clicked.connect(self.cam2)
        self.cam3btn.clicked.connect(self.cam3)
        self.cam4btn.clicked.connect(self.cam4)
        self.cam5btn.clicked.connect(self.cam5)
        self.spbtn.clicked.connect(self.sp)
        ```
    - Define the button of function
    定義當典籍 button 時，會出現什麼樣的功能
        ```python
        def cam1(self):
            ap = argparse.ArgumentParser()
            ap.add_argument("-o", "--output", type=str, default="barcodes.csv",
            help="path to output CSV file containing barcodes")
            args = vars(ap.parse_args())
        ```
    - Demonstrate
    ![](/img/a.gif)

- Label
    - Display video
        ```python
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = QImage(frame, frame.shape[1], frame.shape[0], 
        QImage.Format_Indexed8)
        pixmap = QPixmap.fromImage(image)
        self.label.setPixmap(pixmap)
        ```
- Text Brower
    - Display information
        ```python
        # 繪出影象上的條碼的解碼結果和條碼類別
        barcodeData = barcode.data.decode("utf-8")
        barcodeType = barcode.type
        text = "{} ({})".format(barcodeData, barcodeType)
        cv2.putText(frame, text, (x, y - 10),
        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        self.textBrowser_2.setText(text
        ```
