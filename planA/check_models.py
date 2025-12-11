import google.generativeai as genai
import os  # 新增
from dotenv import load_dotenv  # 新增


# 1. 設定你的 API Key
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("找不到 API Key！請確認你有建立 .env 檔案並設定 GOOGLE_API_KEY")
# 2. 設定 API Key
# 記得去 Google AI Studio 申請 Key
genai.configure(api_key=api_key)

print("正在查詢您的 API Key 可用的模型...\n")

try:
    # 2. 列出所有可用模型
    for m in genai.list_models():
        # 我們只過濾出可以用來 "generateContent" (生成文字/對話) 的模型
        if "generateContent" in m.supported_generation_methods:
            print(f"- 名稱: {m.name}")
            print(f"  描述: {m.description}")
            print("-" * 30)

except Exception as e:
    print(f"發生錯誤，可能是 API Key 無效：{e}")
