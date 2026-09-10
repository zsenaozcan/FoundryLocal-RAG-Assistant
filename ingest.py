import json
from foundry_manager import get_embedding
from database import get_connection


def add_document_to_db(text, source=None):
    """Saves the text and its embedding vector to SQLite."""

    print(f"\nProcessing: '{text[:40]}...'")

    vector = get_embedding(text)
    vector_str = json.dumps(vector)

    print(f"Embedding size: {len(vector)}")
    print("Saving to database...")

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO documents (source, content, embedding)
            VALUES (?, ?, ?)
            """,
            (source, text, vector_str)
        )
        conn.commit()

    print("Success! Text and embedding saved.")


if __name__ == "__main__":
    sample_text = (
        "Microsoft Foundry Local allows you to run AI models offline "
        "on your personal computer, ensuring complete data privacy."
    )
    add_document_to_db(sample_text, source="manual_test")