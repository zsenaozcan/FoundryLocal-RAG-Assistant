import json
import math
from foundry_manager import get_embedding
from database import get_connection


def cosine_similarity(v1, v2, magnitude1=None):
    """Computes the cosine similarity between two vectors.

    If magnitude1 is provided externally (for the query vector), it is not
    recomputed for every document comparison -> removes redundant work
    from inside the loop."""
    dot_product = sum(x * y for x, y in zip(v1, v2))
    if magnitude1 is None:
        magnitude1 = math.sqrt(sum(x * x for x in v1))
    magnitude2 = math.sqrt(sum(y * y for y in v2))
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    return dot_product / (magnitude1 * magnitude2)


def search_database(query, top_k=1):
    """Returns the top_k documents closest to the query as
    (score, content, source) tuples."""
    print(f"\nQuery: '{query}'")
    print("Converting query to a vector...")

    query_vector = get_embedding(query)
    # Compute the query vector's magnitude ONCE, don't repeat it in the loop
    query_magnitude = math.sqrt(sum(x * x for x in query_vector))

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT content, embedding, source FROM documents")
        rows = cursor.fetchall()

    print("Searching the database for the closest match...")
    scored = []
    for content, embedding_str, source in rows:
        doc_vector = json.loads(embedding_str)
        score = cosine_similarity(query_vector, doc_vector, magnitude1=query_magnitude)
        scored.append((score, content, source))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:top_k]


if __name__ == "__main__":
    question = "What is the main advantage of using Microsoft Foundry Local?"
    results = search_database(question, top_k=1)

    for score, content, source in results:
        print(f"\n--- Best Match (Score: {score:.4f}, Source: {source}) ---")
        print(content)
        print("----------------------------------------------------------\n")