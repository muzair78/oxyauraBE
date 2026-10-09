from fastembed import TextEmbedding

# Runs locally — no API, no token, no credits needed
# BAAI/bge-small-en-v1.5 produces 384-dimensional vectors
embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for a list of text chunks using fastembed locally.
    Returns a list of 384-dim float vectors, one per input text.
    """
    if not texts:
        return []

    try:
        embeddings = list(embedding_model.embed(texts))
        return [e.tolist() for e in embeddings]
    except Exception as e:
        print(f"Failed to generate embeddings: {e}")


def get_embedding(text: str) -> list[float]:
    """
    Generate a single embedding vector for one text string.
    Used for query embedding during RAG search.
    """
    return get_embeddings([text])[0]
