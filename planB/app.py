import os
import json
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image
import io

# 1. 初始化
load_dotenv()
app = Flask(__name__)

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("請在 .env 設定 GOOGLE_API_KEY")

genai.configure(api_key=api_key)

# ⭐️ 重點：使用 Flash 模型，並設定回應格式為 JSON (JSON Mode)
# 這樣可以確保 AI 吐出來的一定是乾淨的 JSON，不會有廢話
model = genai.GenerativeModel(
    "gemini-2.5-flash-lite",
    generation_config={"response_mime_type": "application/json"},
)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/scan", methods=["POST"])
def scan_receipt():
    if "file" not in request.files:
        return jsonify({"error": "未上傳圖片"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "檔案名稱為空"}), 400

    try:
        # 2. 處理圖片：讀取檔案並轉為 PIL Image 物件
        image_bytes = file.read()
        image = Image.open(io.BytesIO(image_bytes))

        # 3. 設計 Prompt：明確定義我們要抓取的欄位 (Schema)
        # 告訴 AI 即使圖片很亂，也要盡量萃取這些資訊
        prompt = """
        Analyze this image (invoice, receipt, or quotation).
        Extract the following information and map it to these exact keys:
        
        {
            "vendor": "Company or store name",
            "date": "Date in YYYY-MM-DD format (if uncertain, use today)",
            "inv_number": "Invoice or receipt number (if found)",
            "total": "Total amount (numbers only, remove currency symbols)",
            "items": "A short summary of main items bought (max 10 words)"
        }
        
        If a field is not found, use null or an empty string.
        """

        # 4. 呼叫 Gemini (圖片 + Prompt)
        response = model.generate_content([prompt, image])

        # 5. 回傳結果
        # 因為我們設定了 response_mime_type="application/json"，
        # 所以 response.text 直接就是合法的 JSON 字串
        extracted_data = json.loads(response.text)

        return jsonify(extracted_data)

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5002)
