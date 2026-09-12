import sqlite3

conn = sqlite3.connect("rag_assistant.db")
rows = conn.execute(
    "SELECT source FROM documents WHERE source LIKE '%fight_club%'"
).fetchall()
conn.close()

print(rows)
