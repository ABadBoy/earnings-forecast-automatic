from pathlib import Path


class PdfTextError(RuntimeError):
    pass


def extract_pdf_text(path: Path) -> str:
    extractors = [_extract_with_pypdf, _extract_with_pymupdf, _extract_rough_text]
    errors = []
    for extractor in extractors:
        try:
            text = extractor(path).strip()
        except Exception as exc:  # noqa: BLE001 - optional extractors fail in different ways.
            errors.append(f"{extractor.__name__}: {exc}")
            continue
        if text:
            return text
    raise PdfTextError(f"Unable to extract text from {path}: {'; '.join(errors)}")


def _extract_with_pypdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        from PyPDF2 import PdfReader  # type: ignore[no-redef]

    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _extract_with_pymupdf(path: Path) -> str:
    import fitz

    doc = fitz.open(str(path))
    try:
        return "\n".join(page.get_text("text") for page in doc)
    finally:
        doc.close()


def _extract_rough_text(path: Path) -> str:
    # Last-resort fallback for simple text PDFs. Real production use should install
    # pypdf or PyMuPDF, and add OCR for scanned announcements.
    content = path.read_bytes()
    decoded = content.decode("latin-1", errors="ignore")
    chunks = []
    marker = "stream"
    for part in decoded.split(marker)[1:]:
        stream = part.split("endstream", 1)[0]
        for token in stream.replace("\\n", "\n").splitlines():
            if len(token) >= 8 and any("\u4e00" <= ch <= "\u9fff" for ch in token):
                chunks.append(token.strip())
    return "\n".join(chunks)

