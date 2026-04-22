import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    llm_provider: str
    openai_api_key: str
    openai_model: str
    mistral_api_key: str
    mistral_model: str
    embedding_model: str
    chroma_db_dir: Path
    documents_dir: Path
    retrieval_top_k: int
    flask_secret_key: str
    auto_ingest_on_start: bool
    log_level: str


def load_settings() -> Settings:
    load_dotenv()

    return Settings(
        llm_provider=os.getenv("LLM_PROVIDER", "openai").lower(),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        mistral_api_key=os.getenv("MISTRAL_API_KEY", ""),
        mistral_model=os.getenv("MISTRAL_MODEL", "mistral-small-latest"),
        embedding_model=os.getenv(
            "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        ),
        chroma_db_dir=Path(os.getenv("CHROMA_DB_DIR", "data/chroma")),
        documents_dir=Path(os.getenv("DOCUMENTS_DIR", "data/raw")),
        retrieval_top_k=int(os.getenv("RETRIEVAL_TOP_K", "4")),
        flask_secret_key=os.getenv("FLASK_SECRET_KEY", "dev-secret-key"),
        auto_ingest_on_start=os.getenv("AUTO_INGEST_ON_START", "false").lower()
        == "true",
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
