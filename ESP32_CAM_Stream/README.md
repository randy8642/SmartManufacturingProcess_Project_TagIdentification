# ESP32-CAM 影像傳輸程式

## 程式碼來源
1. [ESP32-CAM Video Streaming Web Server (works with Home Assistant) | Random Nerd Tutorials](https://randomnerdtutorials.com/esp32-cam-video-streaming-web-server-camera-home-assistant/)
2. [RTSP ESP32CAM qnap監視器 錄影測試 @ 夜市小霸王 :: 痞客邦 :: (pixnet.net)](https://youyouyou.pixnet.net/blog/post/120778494-rtsp-esp32cam-qnap%E7%9B%A3%E8%A6%96%E5%99%A8-%E9%8C%84%E5%BD%B1%E6%B8%AC%E8%A9%A6)

## 開始編輯
1. 安裝Arduino IDE
   1. 至 [Arduino 官方網站](https://www.arduino.cc/)
   2. 點擊 Software 即可找到安裝位置
2. 安裝CH340 driver
   1. [ch340 driver](https://sparks.gogo.co.nz/ch340.html)
3. 在Arduino IDE中安裝ESP32驅動\
   安裝方式可參考 **參考資料1 Install ESP32 add-on部分**
4. 匯入Micro-RTSP套件\
    [geeksville/Micro-RTSP](https://github.com/geeksville/Micro-RTSP)\
    安裝方式可參考 **參考資料2 前言部分**

## 燒錄
以RTSP版本為例
1. 開啟 `ESP32_CAM_RTSP.ino` 檔案並更改其中`ssid`以及`password`為要使用的wifi名稱及密碼
    ```cpp
    char *ssid = "<wifi_ssid>";
    char *password = "<wifi_password>";
    ```
2. 編輯 `setup` 中影像品質為需要的品質
    ```cpp
    void setup()
    {
        ...
        //設定影像大小
        esp32cam_aithinker_config.frame_size = FRAMESIZE_VGA;
        esp32cam_aithinker_config.jpeg_quality = 10;
        cam.init(esp32cam_aithinker_config);
        ...
    }
    ```
    選項有
    - `FRAMESIZE_UXGA` (1600x1200)
    - `FRAMESIZE_SXGA` (1280x1024)
    - `FRAMESIZE_XGA` (1024x768)
    - `FRAMESIZE_SVGA` (800x600)
    - `FRAMESIZE_VGA` (640x480)
    - `FRAMESIZE_CIF` (400x296)
    - `FRAMESIZE_QVGA` (320x240)
    - `FRAMESIZE_HQVGA` (240x176)
    - `FRAMESIZE_QQVGA` (160x120)

3. 將板子插入並選擇 `AI Thinker ESP32-CAM`
4. 傳輸時若顯示 `Connect_____` ,則需依序按下板子上的按鈕\
   **壓下FLASH** -> **壓下RST** -> **放開RST** -> **放開FLASH**\
   才能順利寫入
