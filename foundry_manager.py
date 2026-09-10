"""
Singleton manager module for Foundry Local.

Purpose: Perform initialization + model loading ONLY ONCE.
In the previous code, get_embedding() called FoundryLocalManager.initialize()
and embedding_model.load() on every single call, causing the model to be
reloaded from disk each time a document was added -> a serious performance
bottleneck.

ingest.py and search.py now use this module for embeddings.
"""

from foundry_local_sdk import Configuration, FoundryLocalManager

APP_NAME = "rag-assistant"
EMBEDDING_MODEL_ALIAS = "qwen3-embedding-0.6b"
CHAT_MODEL_ALIAS = "qwen2.5-0.5b"

_manager = None
_embedding_model = None
_embedding_client = None
_chat_model = None
_chat_client = None


def _ensure_manager():
    """Initializes FoundryLocalManager only on the first call."""
    global _manager
    if _manager is None:
        print("Starting Foundry Local...")
        FoundryLocalManager.initialize(Configuration(app_name=APP_NAME))
        _manager = FoundryLocalManager.instance
    return _manager


def get_embedding_client():
    """Loads the embedding model only on the first call, returns the cached
    client afterwards."""
    global _embedding_model, _embedding_client

    if _embedding_client is not None:
        return _embedding_client

    manager = _ensure_manager()

    print(f"Loading embedding model: '{EMBEDDING_MODEL_ALIAS}'...")
    _embedding_model = manager.catalog.get_model(EMBEDDING_MODEL_ALIAS)

    if _embedding_model is None:
        raise ValueError(f"Embedding model '{EMBEDDING_MODEL_ALIAS}' could not be found.")

    _embedding_model.load()
    _embedding_client = _embedding_model.get_embedding_client()

    if _embedding_client is None:
        raise RuntimeError("Could not create the embedding client.")

    print("Embedding client ready (you should only see this message ONCE).")
    return _embedding_client


def get_chat_client():
    """Loads the chat model only on the first call, returns the cached
    client afterwards. (Will be used in Week 4 when connecting to the
    local LLM.)"""
    global _chat_model, _chat_client

    if _chat_client is not None:
        return _chat_client

    manager = _ensure_manager()

    print(f"Loading chat model: '{CHAT_MODEL_ALIAS}'...")
    _chat_model = manager.catalog.get_model(CHAT_MODEL_ALIAS)

    if _chat_model is None:
        raise ValueError(f"Chat model '{CHAT_MODEL_ALIAS}' could not be found.")

    _chat_model.download()
    _chat_model.load()
    _chat_client = _chat_model.get_chat_client()

    print("Chat client ready.")
    return _chat_client


def get_embedding(text: str):
    """Converts the given text into an embedding vector."""
    client = get_embedding_client()
    response = client.generate_embedding(text)
    return response.data[0].embedding