import sqlite3
import os
import json
import time
from flask import Flask, request, Response, render_template, stream_with_context
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# 讀取 Key
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    # 如果沒 .env，預設給一個空值或報錯，視你的需求而定
    print("警告: 未偵測到 .env，請確保有設定 API Key")

if api_key:
    genai.configure(api_key=api_key)

# 使用 1.5-flash
model = genai.GenerativeModel("gemini-2.5-flash-lite")


def query_db(query):
    conn = sqlite3.connect("factory.db")
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        columns = [description[0] for description in cursor.description]
        results = cursor.fetchall()
        return [dict(zip(columns, row)) for row in results]
    except Exception as e:
        return str(e)
    finally:
        conn.close()


def get_sql_from_llm(user_question):
    table_schema = """
    Table: production_logs
    Columns: date (Text), factory (Text), batch_no (Text), output (Int), standard (Int)
    """
    prompt = f"""
    You are a SQL expert converting natural language to SQL for SQLite.
    Schema: {table_schema}
    Rules:
    1. Convert: "{user_question}"
    2. Return ONLY raw SQL. No Markdown.
    """
    response = model.generate_content(prompt)
    return response.text.strip().replace("```sql", "").replace("```", "")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    user_question = data.get("question")

    def generate():
        try:
            # 1. 產生 SQL
            generated_sql = get_sql_from_llm(user_question)

            if "DROP" in generated_sql.upper() or "DELETE" in generated_sql.upper():
                yield f"data: {json.dumps({'type': 'error', 'content': '禁止刪除操作'})}\n\n"
                return

            # 2. 查 DB
            db_data = query_db(generated_sql)

            # 3. 先把表格資料推給前端
            init_payload = json.dumps(
                {"type": "init", "sql": generated_sql, "data": db_data},
                ensure_ascii=False,
            )
            yield f"data: {init_payload}\n\n"

            # 4. 開始 AI 總結 (Stream)
            prompt = f"""
            User Question: {user_question}
            Data Retrieved: {str(db_data)}
            Task: Summarize this data in Traditional Chinese (繁體中文). Concise.
            """

            response = model.generate_content(prompt, stream=True)

            for chunk in response:
                if chunk.text:
                    chunk_payload = json.dumps(
                        {"type": "chunk", "content": chunk.text}, ensure_ascii=False
                    )
                    yield f"data: {chunk_payload}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream")


if __name__ == "__main__":
    app.run(debug=True, port=5001)
