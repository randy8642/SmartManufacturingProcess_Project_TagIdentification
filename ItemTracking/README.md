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
4. 