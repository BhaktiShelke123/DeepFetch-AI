"""Multi-format document loader — supports PDF, DOCX, TXT, and Markdown."""

import os
import logging
from pathlib import Path
from typing import Optional

from PyPDF2 import PdfReader
from docx import Document as DocxDocument

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


def load_document(file_path: str) -> dict:
    """Load a single document and return its text + metadata.

    Returns:
        {
            "filename": str,
            "file_type": str,
            "text": str,
            "pages": list[str] | None,   # per-page text if available
            "total_pages": int | None,
        }
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {ext}. "
            f"Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
        )

    loader = {
        ".pdf": _load_pdf,
        ".docx": _load_docx,
        ".txt": _load_text,
        ".md": _load_text,
    }[ext]

    logger.info(f"Loading {path.name} ({ext})")
    return loader(path)


def load_directory(directory: str) -> list[dict]:
    """Load all supported documents from a directory."""
    docs = []
    dir_path = Path(directory)

    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    for file_path in sorted(dir_path.iterdir()):
        if file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
            try:
                doc = load_document(str(file_path))
                docs.append(doc)
                logger.info(
                    f"  ✓ {doc['filename']} — "
                    f"{doc.get('total_pages', '?')} pages"
                )
            except Exception as e:
                logger.error(f"  ✗ Failed to load {file_path.name}: {e}")

    logger.info(f"Loaded {len(docs)} documents from {directory}")
    return docs


# ── Format-specific loaders ──────────────────────────────────────────────


def _load_pdf(path: Path) -> dict:
    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text.strip())

    return {
        "filename": path.name,
        "file_type": "pdf",
        "text": "\n\n".join(pages),
        "pages": pages,
        "total_pages": len(pages),
    }


def _load_docx(path: Path) -> dict:
    doc = DocxDocument(str(path))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    full_text = "\n\n".join(paragraphs)

    return {
        "filename": path.name,
        "file_type": "docx",
        "text": full_text,
        "pages": None,
        "total_pages": None,
    }


def _load_text(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")

    return {
        "filename": path.name,
        "file_type": path.suffix.lstrip("."),
        "text": text,
        "pages": None,
        "total_pages": None,
    }
