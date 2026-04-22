import logging
import os

from flask import Flask, jsonify, render_template, request

from src.config import Settings, load_settings
from src.ingest import ingest_documents
from src.rag_chain import RAGService


def create_app() -> Flask:
    settings = load_settings()
    configure_logging(settings.log_level)

    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.flask_secret_key

    if settings.auto_ingest_on_start:
        logging.info("AUTO_INGEST_ON_START enabled. Building vector store.")
        ingest_documents(settings)

    rag_service = RAGService(settings)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.post("/chat")
    def chat():
        payload = request.get_json(silent=True) or {}
        message = (payload.get("message") or "").strip()
        session_id = (payload.get("session_id") or "default").strip()

        if not message:
            return jsonify({"error": "Message is required."}), 400

        try:
            result = rag_service.answer(message=message, session_id=session_id)
            return jsonify(result)
        except ValueError as exc:
            logging.warning("Chat validation error: %s", exc)
            return jsonify({"error": str(exc)}), 400
        except Exception:
            logging.exception("Unexpected chat error")
            return jsonify(
                {
                    "error": (
                        "The assistant could not process the request right now. "
                        "Please try again or contact support."
                    )
                }
            ), 500

    return app


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
