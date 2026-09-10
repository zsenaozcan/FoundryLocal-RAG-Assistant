import sqlite3
from contextlib import contextmanager

DB_NAME = "rag_assistant.db"


def init_db(db_name=DB_NAME):
    """Initializes the SQLite database and creates the required table."""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # source column: stores which file each chunk came from
    # (needed for the "show sources" feature planned for Week 4)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            content TEXT NOT NULL,
            embedding TEXT NOT NULL
        )
    ''')

    conn.commit()
    return conn


@contextmanager
def get_connection(db_name=DB_NAME):
    """Safely opens and closes the connection inside a 'with' block.
    conn.close() is guaranteed to run even if an error occurs."""
    conn = init_db(db_name)
    try:
        yield conn
    finally:
        conn.close()


if __name__ == "__main__":
    print("Setting up the database...")
    with get_connection():
        pass
    print("Database and table created successfully!")