import sqlite3

conn = sqlite3.connect("app.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE help_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT,
    done_date DATE
)
""")

cur.execute("""
INSERT INTO help_log(content, done_date)
VALUES
('おふろそうじ', '2026-04-10')
""")

cur.execute("""
INSERT INTO help_log(content, done_date)
VALUES
('お皿洗い', '2026-04-10')
""")

conn.commit()
conn.close()

print("DB作成完了")