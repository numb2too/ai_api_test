import os
import json
import time
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

app = Flask(__name__)

# 設定上傳暫存資料夾
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

# 使用 gemini-1.5-flash (支援音訊輸入且便宜快速)
model = genai.GenerativeModel("gemini-2.5-flash-lite")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze_meeting():
    # 1. 檢查是否有檔案
    if "audio" not in request.files:
        return jsonify({"error": "未上傳音訊檔案"}), 400

    file = request.files["audio"]
    if file.filename == "":
        return jsonify({"error": "檔案名稱為空"}), 400

    # 2. 儲存檔案到本地 (暫存)
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    try:
        # 3. 上傳檔案到 Gemini File API
        # 面試亮點：我們利用 Gemini 原生多模態能力，不需額外掛載 Whisper
        print(f"正在上傳至 Google AI: {file.filename}...")
        uploaded_file = genai.upload_file(path=file_path)

        # 等待檔案處理完成 (通常音訊處理很快)
        while uploaded_file.state.name == "PROCESSING":
            time.sleep(1)
            uploaded_file = genai.get_file(uploaded_file.name)

        if uploaded_file.state.name == "FAILED":
            raise ValueError("Google AI 檔案處理失敗")

        # 4. Prompt Engineering (針對音訊)
        prompt = """
        You are a professional meeting secretary. 
        Listen to the attached meeting recording carefully.

        Tasks:
        1. Summarize the meeting (around 200 words) in Traditional Chinese.
        2. Extract actionable tasks.

        Return strictly valid JSON:
        {
            "summary": "...",
            "action_items": [
                {
                    "owner": "Name (or 'Unknown')",
                    "task": "Task description in Traditional Chinese",
                    "deadline": "Deadline or 'TBD'"
                }
            ]
        }
        """

        # 5. 發送請求 (Prompt + Audio File)
        response = model.generate_content(
            [prompt, uploaded_file],
            generation_config={"response_mime_type": "application/json"},
        )

        # 6. 清理：刪除 Google 端與本地端的暫存檔 (節省空間與隱私)
        # 註：面試時可以說 "為了 Demo 簡單我們先不刪 Google 端的檔案，實際專案建議用 uploaded_file.delete()"
        try:
            os.remove(file_path)
        except:
            pass

        return jsonify(json.loads(response.text))

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5005)
