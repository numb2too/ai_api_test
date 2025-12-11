
```bash
# 1. 建立名為 venv 的虛擬環境
python -m venv venv

# 2. 啟動虛擬環境
# Mac/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate
```

```bash
pip install -r requirements.txt
```
> 產生 requirements.txt `pip freeze > requirements.txt`

```bash
dev.env
GOOGLE_API_KEY=你的 API Key
```

```bash
# 確保已啟動虛擬環境並安裝套件
# 先執行 init_db.py 產生 factory.db
python init_db.py
# 執行 app.py 即可運行
python app.py
```

![alt text](image.png)