import sqlite3


def init_db():
    # 建立一個本地檔案型資料庫 'factory.db'
    conn = sqlite3.connect("factory.db")
    cursor = conn.cursor()

    # 1. 建立資料表 (模擬大甲廠的生產紀錄)
    # 欄位：id, date(日期), factory(廠區), batch_no(批號), output(產量), standard(標準產量)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS production_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            factory TEXT,
            batch_no TEXT,
            output INTEGER,
            standard INTEGER
        )
    """
    )

    # 2. 塞入假資料 (包含一些低於標準的數據，讓你的 Demo 查得到東西)
    data = [
        ("2023-10-01", "大甲廠", "DJ-001", 950, 1000),  # 低於標準
        ("2023-10-02", "大甲廠", "DJ-002", 1050, 1000),
        ("2023-10-03", "大甲廠", "DJ-003", 1020, 1000),
        ("2023-10-05", "大甲廠", "DJ-004", 880, 1000),  # 低於標準
        ("2023-10-05", "二林廠", "EL-001", 1100, 1000),
        ("2023-10-10", "大甲廠", "DJ-005", 900, 1000),  # 低於標準
    ]

    cursor.executemany(
        """
        INSERT INTO production_logs (date, factory, batch_no, output, standard)
        VALUES (?, ?, ?, ?, ?)
    """,
        data,
    )

    conn.commit()
    conn.close()
    print("假資料庫 factory.db 建立完成！")


if __name__ == "__main__":
    init_db()
