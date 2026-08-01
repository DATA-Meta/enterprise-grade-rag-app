"""
Document ingestion: load raw files from a folder and split them into chunks.

Supported for now: .txt, .pdf
(We'll add .docx, .pptx, .html in a follow-up step once this is working.)
"""

from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


@dataclass
class Document:
    """One loaded file, before chunking."""
    source: str   # filename, so we can trace a chunk back to its origin
    text: str     # full raw text of the file


@dataclass
class Chunk:
    """One chunk of a document, ready to be embedded."""
    source: str
    chunk_id: int
    text: str


def load_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def load_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)


def load_documents(data_dir: str) -> list[Document]:
    """
    Read every supported file in `data_dir` and return a list of Document objects.
    """
    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    documents: list[Document] = []

    for file_path in data_path.iterdir():
        if not file_path.is_file():
            continue

        suffix = file_path.suffix.lower()

        if suffix == ".txt":
            text = load_txt(file_path)
        elif suffix == ".pdf":
            text = load_pdf(file_path)
        else:
            # Unsupported file type for now — skip it rather than crash.
            continue

        if text.strip():
            documents.append(Document(source=file_path.name, text=text))

    return documents


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 150) -> list[str]:
    """
    Split text into overlapping chunks of roughly `chunk_size` characters.

    Overlap means the last `overlap` characters of one chunk are repeated at
    the start of the next chunk, so we don't lose context at chunk boundaries
    (e.g. a sentence that would otherwise be cut in half).
    """
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap")

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap  # step forward, but re-include the overlap

    return chunks


def chunk_documents(documents: list[Document], chunk_size: int = 1000, overlap: int = 150) -> list[Chunk]:
    """
    Turn a list of Documents into a flat list of Chunks, ready for embedding.
    """
    all_chunks: list[Chunk] = []

    for doc in documents:
        pieces = chunk_text(doc.text, chunk_size=chunk_size, overlap=overlap)
        for i, piece in enumerate(pieces):
            all_chunks.append(Chunk(source=doc.source, chunk_id=i, text=piece))

    return all_chunks


if __name__ == "__main__":
    # Quick manual test: point this at your DATA folder and print a summary.
    docs = load_documents("DATA")
    print(f"Loaded {len(docs)} document(s).")

    chunks = chunk_documents(docs)
    print(f"Produced {len(chunks)} chunk(s).")

    if chunks:
        print("\n--- First chunk preview ---")
        print(f"Source: {chunks[0].source} | Chunk ID: {chunks[0].chunk_id}")
        print(chunks[0].text[:300])