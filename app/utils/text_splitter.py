from langchain_text_splitters import RecursiveCharacterTextSplitter


# Splitter instance — reused across all calls
_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,       # max characters per chunk
    chunk_overlap=50,     # overlap between consecutive chunks
    separators=[
        "\n\n",   # paragraph breaks  (tried first)
        "\n",     # line breaks
        " ",      # word boundaries
        "",       # character-level   (last resort)
    ],
)


def split_text(text: str) -> list[str]:
    """
    Split extracted document text into overlapping chunks using
    RecursiveCharacterTextSplitter.

    Returns a list of non-empty string chunks.
    """
    if not text or not text.strip():
        return []

    chunks = _splitter.split_text(text)

    # Filter out any empty/whitespace-only chunks
    return [c.strip() for c in chunks if c.strip()]
