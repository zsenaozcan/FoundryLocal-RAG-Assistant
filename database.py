import sqlite3

def init_db(db_name="rag_assistant.db"):
    """Initializes the SQLite database and creates the necessary tables."""
    print(f"Connecting to database: {db_name}")
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # Create a table for storing documents and their embeddings
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            embedding TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    return conn

if __name__ == "__main__":
    print("Initializing database setup...")
    conn = init_db()
    print("Database and tables created successfully!")
    conn.close()
    