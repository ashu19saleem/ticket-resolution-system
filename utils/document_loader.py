"""
Multi-format document loaders for the knowledge base.
Supports PDF, DOCX, TXT/MD, and CSV (handled separately for tickets).
"""

from pathlib import Path
from typing import List, Dict


def load_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def load_pdf(path: Path) -> str:
    from pypdf import PdfReader
    reader = PdfReader(str(path))
    text_parts = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(text_parts)


def load_docx(path: Path) -> str:
    import docx
    document = docx.Document(str(path))
    return "\n".join(p.text for p in document.paragraphs)


_LOADERS = {
    ".txt": load_txt,
    ".md": load_txt,
    ".pdf": load_pdf,
    ".docx": load_docx,
}


def load_document(path: Path) -> str:
    """Dispatch to the right loader based on file extension."""
    suffix = path.suffix.lower()
    loader = _LOADERS.get(suffix)
    if loader is None:
        raise ValueError(
            f"Unsupported file type '{suffix}' for {path.name}. "
            f"Supported: {list(_LOADERS.keys())}"
        )
    return loader(path)


def load_documents_from_dir(directory: Path) -> List[Dict[str, str]]:
    """
    Load every supported document in a directory.
    Returns list of {"source": filename, "text": content}.
    Files that fail to parse are skipped with a printed warning rather
    than crashing the whole ingestion run.
    """
    results = []
    if not directory.exists():
        return results

    for path in sorted(directory.iterdir()):
        if path.is_file() and path.suffix.lower() in _LOADERS:
            try:
                text = load_document(path)
                if text.strip():
                    results.append({"source": path.name, "text": text})
            except Exception as e:
                print(f"[WARN] Skipping {path.name}: {e}")

    return results
