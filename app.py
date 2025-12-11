import sqlite3
import os
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai  # 1. 改用 Google 的套件
import os  # 新增
from dotenv import load_dotenv  # 新增

# 1. 載入 .env 檔案中的變數
load_dotenv()
app = Flask(__name__)

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("找不到 API Key！請確認你有建立 .env 檔案並設定 GOOGLE_API_KEY")
# 2. 設定 API Key
# 記得去 Google AI Studio 申請 Key
genai.configure(api_key=api_key)

# 初始化模型，推薦使用 gemini-1.5-flash (速度快、免費額度高) 或 gemini-1.5-pro (更聰明)
model = genai.GenerativeModel("gemini-2.5-flash")


def query_db(query):
    """(這段完全不用改) 執行 SQL 並回傳結果"""
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
    """
    改寫：使用 Gemini 產生 SQL
    """
    table_schema = """
    Table: production_logs
    Columns: date (Text), factory (Text), batch_no (Text), output (Int), standard (Int)
    """

    # Gemini 的 Prompt 寫法
    prompt = f"""
    You are a SQL expert converting natural language to SQL for SQLite.
    
    Schema:
    {table_schema}
    
    Rules:
    1. Convert this question: "{user_question}"
    2. Return ONLY the raw SQL query. 
    3. Do NOT use Markdown formatting (no ```sql ... ```). 
    4. Do NOT add explanations.
    """

    # 呼叫 Gemini
    response = model.generate_content(prompt)

    # 清理結果 (Gemini有時候很雞婆會加 Markdown 符號，我們手動清掉以防萬一)
    sql_query = response.text.strip().replace("```sql", "").replace("```", "")
    return sql_query


def summarize_results(user_question, data):
    """
    改寫：使用 Gemini 總結數據
    """
    prompt = f"""
    User Question: {user_question}
    Data Retrieved: {str(data)}
    
    Task: Summarize this data in Traditional Chinese (繁體中文) for a factory manager. 
    Keep it concise (within 50 words).
    """

    response = model.generate_content(prompt)
    return response.text


# --- 以下路由 (Routes) 完全不用改 ---


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/ask", methods=["POST"])
def ask():
    user_question = request.json.get("question")

    # 1. 翻譯成 SQL
    generated_sql = get_sql_from_llm(user_question)
    print(f"Gemini Generated SQL: {generated_sql}")

    # 2. 執行 SQL (安全檢查)
    if "DROP" in generated_sql.upper() or "DELETE" in generated_sql.upper():
        return jsonify({"error": "為了 Demo 安全，禁止刪除操作！"})

    data = query_db(generated_sql)

    # 3. 總結結果
    summary = summarize_results(user_question, data)

    return jsonify({"sql": generated_sql, "data": data, "summary": summary})


if __name__ == "__main__":
    app.run(debug=True, port=5001)
