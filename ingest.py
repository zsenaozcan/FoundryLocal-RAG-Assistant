import json
from foundry_local_sdk import Configuration, FoundryLocalManager
from database import init_db


def get_embedding(text):
    """Generate an embedding vector using Microsoft Foundry Local."""

    print("Initializing Foundry Local for Embedding...")

    # Start Foundry Local
    FoundryLocalManager.initialize(
        Configuration(app_name="rag-assistant")
    )

    # Get the Foundry Local manager
    manager = FoundryLocalManager.instance

    # Your installed Foundry Local catalog contains
    # this embedding model under this exact alias.
    model_alias = "qwen3-embedding-0.6b"

    print(f"Loading embedding model: '{model_alias}'...")

    # Get the embedding model using its alias
    embedding_model = manager.catalog.get_model(model_alias)

    if embedding_model is None:
        raise ValueError(
            f"Embedding model '{model_alias}' could not be found."
        )

    print("Embedding model found.")

    # Load the model
    print("Loading model...")
    embedding_model.load()

    print("Model loaded.")

    # Get the embedding client
    print("Creating embedding client...")
    embedding_client = embedding_model.get_embedding_client()

    if embedding_client is None:
        raise RuntimeError(
            "Could not create the embedding client."
        )

    print("Embedding client created.")

    # Generate the embedding
    print("Converting text to vector...")

    response = embedding_client.generate_embedding(text)

    # Extract the vector
    embedding = response.data[0].embedding

    print(
        f"Embedding generated successfully. "
        f"Vector size: {len(embedding)}"
    )

    return embedding


def add_document_to_db(text):
    """Save the text and its embedding vector to SQLite."""

    print(f"\nProcessing text: '{text[:40]}...'")

    # Generate embedding
    vector = get_embedding(text)

    # Convert vector to JSON
    vector_str = json.dumps(vector)

    print("Saving text and embedding to database...")

    # Connect to SQLite database
    conn = init_db()
    cursor = conn.cursor()

    # Insert document and embedding
    cursor.execute(
        """
        INSERT INTO documents (content, embedding)
        VALUES (?, ?)
        """,
        (text, vector_str)
    )

    conn.commit()
    conn.close()

    print("Success! Document and its embedding are saved.")


if __name__ == "__main__":
    sample_text = (
        "Microsoft Foundry Local allows you to run AI models offline "
        "on your personal computer, ensuring complete data privacy."
    )

    add_document_to_db(sample_text)