import os
import json
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import google.generativeai as genai

# 載入環境變數
load_dotenv()

app = Flask(__name__)

# 設定 Gemini
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("警告：未偵測到 GOOGLE_API_KEY")

genai.configure(api_key=api_key)

# 使用支援 JSON mode 的模型 (Gemini 1.5 Flash 既快又便宜，適合此場景)
model = genai.GenerativeModel("gemini-2.5-flash-lite")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze_meeting():
    data = request.json
    transcript = data.get("transcript", "")

    if not transcript:
        return jsonify({"error": "請提供會議逐字稿"}), 400

    # --- Prompt Engineering (關鍵) ---
    # 我們要求 AI 扮演秘書，並嚴格輸出 JSON 格式
    prompt = f"""
    You are a professional meeting secretary. 
    Analyze the following meeting transcript and extract key information.

    Transcript:
    {transcript}

    Please return the result in strictly valid JSON format with the following structure:
    {{
        "summary": "A concise summary of the meeting (around 200 words) in Traditional Chinese.",
        "action_items": [
            {{
                "owner": "Name of the person responsible (or 'Unknown')",
                "task": "Description of the task in Traditional Chinese",
                "deadline": "Mentioned deadline or 'TBD' (To Be Determined)"
            }},
            ...
        ]
    }}
    
    IMPORTANT: Return ONLY the JSON. Do not use Markdown code blocks.
    """

    try:
        # 設定 generation_config 強制回傳 application/json (這是 Gemini 的新功能，讓解析更穩)
        response = model.generate_content(
            prompt, generation_config={"response_mime_type": "application/json"}
        )

        # 解析 AI 回傳的 JSON 字串
        result_json = json.loads(response.text)

        return jsonify(result_json)

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "AI 分析失敗，請稍後再試"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5004)
