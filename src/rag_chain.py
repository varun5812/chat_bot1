from collections import defaultdict, deque
from typing import Deque

from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI

from src.config import Settings


SUPPORT_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""You are a helpful customer support assistant.

Use only the provided context to answer the customer question.
If the context does not contain the answer, say that the knowledge base does not include that information.
Do not invent policies, prices, timelines, or support commitments.
Keep the answer concise, friendly, and actionable.

Context:
{context}

Customer question:
{question}

Answer:""",
)


class RAGService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.embeddings = HuggingFaceEmbeddings(model_name=settings.embedding_model)
        self.vector_store = Chroma(
            persist_directory=str(settings.chroma_db_dir),
            embedding_function=self.embeddings,
            collection_name="customer_support_kb",
        )
        self.llm = self._build_llm()
        self.history: dict[str, Deque[tuple[str, str]]] = defaultdict(
            lambda: deque(maxlen=6)
        )

        retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": settings.retrieval_top_k},
        )

        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": SUPPORT_PROMPT},
        )

    def _build_llm(self):
        if self.settings.llm_provider == "openai":
            if not self.settings.openai_api_key:
                raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai.")
            return ChatOpenAI(
                api_key=self.settings.openai_api_key,
                model=self.settings.openai_model,
                temperature=0.2,
            )

        if self.settings.llm_provider == "mistral":
            if not self.settings.mistral_api_key:
                raise ValueError("MISTRAL_API_KEY is required when LLM_PROVIDER=mistral.")
            try:
                from langchain_mistralai import ChatMistralAI
            except ImportError as exc:
                raise ValueError(
                    "Mistral support is optional for deployment. Add "
                    "'langchain-mistralai' to requirements.txt to use LLM_PROVIDER=mistral."
                ) from exc
            return ChatMistralAI(
                api_key=self.settings.mistral_api_key,
                model=self.settings.mistral_model,
                temperature=0.2,
            )

        raise ValueError("LLM_PROVIDER must be either 'openai' or 'mistral'.")

    def answer(self, message: str, session_id: str = "default") -> dict:
        question = self._format_question_with_history(message, session_id)
        response = self.qa_chain.invoke({"query": question})

        answer = response["result"].strip()
        self.history[session_id].append((message, answer))

        return {
            "answer": answer,
            "sources": self._format_sources(response.get("source_documents", [])),
        }

    def similarity_search(self, query: str, k: int | None = None):
        return self.vector_store.similarity_search(
            query, k=k or self.settings.retrieval_top_k
        )

    def _format_question_with_history(self, message: str, session_id: str) -> str:
        if not self.history[session_id]:
            return message

        turns = []
        for user_message, assistant_answer in self.history[session_id]:
            turns.append(f"Customer: {user_message}\nAssistant: {assistant_answer}")

        history_text = "\n".join(turns)
        return f"Conversation history:\n{history_text}\n\nLatest question: {message}"

    @staticmethod
    def _format_sources(source_documents) -> list[dict]:
        sources = []
        for doc in source_documents:
            sources.append(
                {
                    "source": doc.metadata.get("source", "unknown"),
                    "page": doc.metadata.get("page"),
                    "snippet": doc.page_content[:350],
                }
            )
        return sources
