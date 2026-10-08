import io
import pdfplumber
from docx import Document


def extract_text(file_bytes: bytes, content_type: str, filename: str) -> str:
    """
    Extract plain text from a file based on its content type.

    Supported formats:
      - PDF  → pdfplumber
      - DOCX → python-docx
      - TXT  → direct decode
    """
    content_type = content_type or ""
    filename = filename or ""

    # ── PDF ──────────────────────────────────────────────────────────────────
    if "pdf" in content_type or filename.lower().endswith(".pdf"):
        return _extract_from_pdf(file_bytes)

    # ── DOCX ─────────────────────────────────────────────────────────────────
    if (
        "wordprocessingml" in content_type
        or "msword" in content_type
        or filename.lower().endswith(".docx")
        or filename.lower().endswith(".doc")
    ):
        return _extract_from_docx(file_bytes)

    # ── Plain text ────────────────────────────────────────────────────────────
    if "text" in content_type or filename.lower().endswith(".txt"):
        return file_bytes.decode("utf-8", errors="ignore")

    raise ValueError(
        f"Unsupported file type: '{content_type}' / '{filename}'. "
        "Only PDF, DOCX, and TXT files are supported."
    )


def _extract_from_pdf(file_bytes: bytes) -> str:
    """Extract all text from a PDF using pdfplumber."""
    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text.strip())
    return "\n\n".join(text_parts)


def _extract_from_docx(file_bytes: bytes) -> str:
    """Extract all paragraph text from a DOCX file."""
    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)
