import logging
import shutil
from pathlib import Path
from typing import Iterable

from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.document_loaders import (
    CSVLoader,
    PyPDFLoader,
    TextLoader,
)
from langchain_huggingface import HuggingFaceEmbeddings

from src.config import Settings, load_settings


SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".csv"}


def load_documents(documents_dir: Path) -> list[Document]:
    documents: list[Document] = []

    for path in iter_supported_files(documents_dir):
        loader = build_loader(path)
        loaded_docs = loader.load()
        for doc in loaded_docs:
            doc.metadata["source"] = str(path)
        documents.extend(loaded_docs)

    return documents


def iter_supported_files(documents_dir: Path) -> Iterable[Path]:
    if not documents_dir.exists():
        raise FileNotFoundError(f"Documents directory does not exist: {documents_dir}")

    for path in sorted(documents_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield path


def build_loader(path: Path):
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return PyPDFLoader(str(path))
    if suffix == ".csv":
        return CSVLoader(str(path))
    if suffix == ".md":
        return TextLoader(str(path), encoding="utf-8")
    if suffix == ".txt":
        return TextLoader(str(path), encoding="utf-8")

    raise ValueError(f"Unsupported file type: {path}")


def split_documents(documents: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=150,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_documents(documents)


def ingest_documents(settings: Settings) -> int:
    logging.info("Loading documents from %s", settings.documents_dir)
    documents = load_documents(settings.documents_dir)

    if not documents:
        raise ValueError(
            f"No supported documents found in {settings.documents_dir}. "
            f"Supported extensions: {sorted(SUPPORTED_EXTENSIONS)}"
        )

    chunks = split_documents(documents)
    logging.info("Loaded %s documents and created %s chunks", len(documents), len(chunks))

    embeddings = HuggingFaceEmbeddings(model_name=settings.embedding_model)
    reset_vector_store(settings.chroma_db_dir)
    settings.chroma_db_dir.mkdir(parents=True, exist_ok=True)

    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(settings.chroma_db_dir),
        collection_name="customer_support_kb",
    )

    logging.info("Stored embeddings in %s", settings.chroma_db_dir)
    return len(chunks)


def reset_vector_store(chroma_db_dir: Path) -> None:
    if chroma_db_dir.exists():
        logging.info("Clearing existing vector store at %s", chroma_db_dir)
        shutil.rmtree(chroma_db_dir)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
    settings = load_settings()
    chunk_count = ingest_documents(settings)
    print(f"Ingestion complete. Stored {chunk_count} chunks in ChromaDB.")


if __name__ == "__main__":
    main()
