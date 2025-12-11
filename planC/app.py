import os
import chromadb
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template
from pypdf import PdfReader
from dotenv import load_dotenv

# 載入 .env
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# 初始化 Gemini
genai.configure(api_key=api_key)

app = Flask(__name__)

# --- 初始化向量資料庫 (ChromaDB) ---
# 這會在你專案目錄下建立一個 'factory_knowledge_db' 資料夾來存資料
chroma_client = chromadb.PersistentClient(path="./factory_knowledge_db")

# 建立一個 Collection (類似 SQL 的 Table)，名字叫 'manuals'
# 如果已經存在就直接讀取
collection = chroma_client.get_or_create_collection(name="manuals")


def get_embedding(text):
    """
    將文字轉成向量 (Vector)
    使用模型: text-embedding-004 (Google 專門做嵌入的模型)
    """
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=text,
        task_type="retrieval_document",
    )
    return result["embedding"]


def get_query_embedding(text):
    """
    將使用者的問題轉成向量
    """
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=text,
        task_type="retrieval_query",
    )
    return result["embedding"]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload_pdf", methods=["POST"])
def upload_pdf():
    """
    步驟 1：上傳 PDF -> 讀取文字 -> 切塊 -> 存入向量資料庫
    """
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "未上傳檔案"}), 400

    # 1. 讀取 PDF 文字
    pdf = PdfReader(file)
    text_chunks = []

    # 簡單的切塊邏輯：以「頁」為單位 (實務上通常會每 500 字切一段)
    for i, page in enumerate(pdf.pages):
        text = page.extract_text()
        if text:
            # 加上頁碼標記，方便之後引用
            chunk_data = {
                "id": f"{file.filename}_page_{i+1}",
                "text": text,
                "source": f"{file.filename} 第 {i+1} 頁",
            }
            text_chunks.append(chunk_data)

    # 2. 轉成向量並存入 ChromaDB
    # 注意：大量資料時應該分批處理，避免 API 超時
    for chunk in text_chunks:
        # 呼叫 Google Embedding API
        vector = get_embedding(chunk["text"])

        # 存入資料庫
        collection.upsert(
            ids=[chunk["id"]],  # 唯一 ID
            embeddings=[vector],  # 向量數據
            documents=[chunk["text"]],  # 原始文字內容
            metadatas=[{"source": chunk["source"]}],  # 額外資訊
        )

    return jsonify({"message": f"成功處理 {len(text_chunks)} 個頁面並存入知識庫！"})


@app.route("/ask_rag", methods=["POST"])
def ask_rag():
    """
    步驟 2：搜尋向量資料庫 -> 組裝 Prompt -> 讓 AI 回答
    """
    user_question = request.json.get("question")

    # 1. 把使用者的問題變成向量
    query_vector = get_query_embedding(user_question)

    # 2. 去 ChromaDB 搜尋「最像」的 3 個段落
    results = collection.query(
        query_embeddings=[query_vector], n_results=3  # 找前 3 名
    )

    # 取出找到的文字與來源
    retrieved_texts = results["documents"][0]  # List of strings
    retrieved_sources = results["metadatas"][0]  # List of dicts

    # 3. 組合 Prompt (這就是 RAG 的精髓：把資料餵給 AI)
    context_str = "\n\n".join(retrieved_texts)
    source_str = ", ".join([m["source"] for m in retrieved_sources])

    prompt = f"""
    你是工廠的資深維修顧問。請根據以下的【參考資料】回答使用者的問題。
    如果參考資料沒有提到相關內容，請直接說「資料庫中找不到相關資訊」，不要瞎掰。

    【參考資料】：
    {context_str}

    【使用者問題】：
    {user_question}

    請用繁體中文回答，並在最後標註資訊來源：({source_str})
    """

    # 4. 呼叫 Gemini 回答
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)

    return jsonify({"answer": response.text, "sources": retrieved_sources})


if __name__ == "__main__":
    app.run(debug=True, port=5003)
