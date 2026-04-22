# Generative AI Chatbot for Customer Support Automation

Production-ready customer support chatbot built with a Retrieval-Augmented Generation (RAG) architecture. The bot answers customer questions using internal documents, FAQs, and policy files instead of relying only on the LLM's pre-trained knowledge.

## 1. Architecture: How The RAG Pipeline Works

RAG combines search with generation:

1. **Customer asks a question**
   - Example: "How do I request a refund?"
   - The question is not sent directly to the LLM alone because that can cause hallucinations.

2. **Retriever searches internal knowledge**
   - Documents are loaded from `data/raw`.
   - Text is split into smaller chunks.
   - Each chunk is converted into embeddings using Sentence Transformers.
   - Chunks and embeddings are stored in ChromaDB.
   - At query time, ChromaDB returns the most relevant chunks.

3. **Prompt combines context and question**
   - The app builds a prompt containing:
     - retrieved document context
     - conversation history
     - user question
     - rules for safe answering

4. **LLM generates the final answer**
   - GPT-3.5, GPT-4 compatible OpenAI models, or Mistral can be used.
   - The LLM is instructed to answer only from retrieved context and say when information is unavailable.

5. **Flask returns the response**
   - `/chat` accepts a user message and returns JSON with the answer and retrieved sources.
   - The included HTML page gives a simple chatbot UI.

Why this architecture matters in interviews:

- **Accuracy:** Retrieval grounds the answer in company documents.
- **Maintainability:** Updating documents updates chatbot knowledge without retraining.
- **Transparency:** Returned source chunks make answers explainable.
- **Production readiness:** API keys, logging, error handling, and deployment files are separated from code.

## 2. Folder Structure

```text
chat_bot/
  app.py
  requirements.txt
  Procfile
  render.yaml
  .env.example
  .gitignore
  README.md
  data/
    raw/
      faq.txt
    chroma/
      .gitkeep
  src/
    __init__.py
    config.py
    ingest.py
    rag_chain.py
  templates/
    index.html
  static/
    css/
      style.css
    js/
      chat.js
```

## 3. Local Setup

Create and activate a virtual environment:

```bash
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create your environment file:

```bash
copy .env.example .env
```

On macOS/Linux:

```bash
cp .env.example .env
```

Then edit `.env` and add either OpenAI or Mistral settings.

## 4. Environment Variables

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-3.5-turbo

MISTRAL_API_KEY=your_mistral_api_key
MISTRAL_MODEL=mistral-small-latest

EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
CHROMA_DB_DIR=data/chroma
DOCUMENTS_DIR=data/raw
RETRIEVAL_TOP_K=4
FLASK_SECRET_KEY=change-this-secret
```

Why `.env` is used:

- Keeps secrets out of source code.
- Makes deployment easier because Render can inject the same values.
- Allows switching providers without rewriting the app.

## 5. Data Ingestion

Put PDFs, `.txt`, `.md`, or `.csv` files into:

```text
data/raw/
```

Then run:

```bash
python -m src.ingest
```

What ingestion does:

- Loads documents from disk.
- Splits large text into chunks so retrieval stays precise.
- Converts chunks into embeddings.
- Stores vectors and metadata in ChromaDB.

Why chunking is important:

- LLMs have context limits.
- Smaller chunks improve search relevance.
- Overlap preserves meaning across chunk boundaries.

## 6. Run The App

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

API example:

```bash
curl -X POST http://127.0.0.1:5000/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"How do I reset my password?\"}"
```

## 7. Example Questions And Expected Outputs

Question:

```text
How do I reset my password?
```

Expected answer:

```text
You can reset your password from the login page by selecting "Forgot password" and following the email reset link.
```

Question:

```text
What is the refund policy?
```

Expected answer:

```text
Refunds are available within 30 days for eligible purchases. The customer should contact support with the order ID.
```

Question:

```text
Can I get phone support at midnight?
```

Expected answer:

```text
The knowledge base does not mention midnight phone support. Support is available Monday to Friday from 9 AM to 6 PM.
```

## 8. Key Components

### Document Loader

Loads internal knowledge files from `data/raw`.

Why:

- The chatbot needs trusted company content.
- Different loaders support different document formats.

### Text Splitter

Splits documents into chunks with overlap.

Why:

- Retrieval works better on focused text.
- Overlap reduces the chance of losing context between chunks.

### Embeddings

Uses Sentence Transformers to convert text into numeric vectors.

Why:

- Similar meaning produces nearby vectors.
- This enables semantic search instead of keyword-only search.

### ChromaDB

Stores embeddings and document metadata locally.

Why:

- Fast similarity search.
- Persistent storage between app restarts.
- Simple enough for a portfolio project and deployable on Render disk storage.

### Retriever

Searches ChromaDB for the top-k most relevant chunks.

Why:

- Only the most relevant context is sent to the LLM.
- Reduces token cost and improves answer quality.

### Prompt Template

Controls how the LLM behaves.

Why:

- Reduces hallucination.
- Enforces concise, customer-support style answers.
- Tells the LLM to admit when the answer is not in the documents.

### Flask Backend

Exposes `/chat` and serves the UI.

Why:

- Simple deployment path.
- Easy to test with Postman, curl, or frontend JavaScript.

## 9. Optimization Ideas

Improve retrieval accuracy:

- Add more high-quality FAQs and policy documents.
- Tune `RETRIEVAL_TOP_K`.
- Tune chunk size and overlap in `src/ingest.py`.
- Remove duplicate or outdated documents.
- Add metadata such as product, category, or policy version.

Reduce hallucinations:

- Keep the prompt strict.
- Return "I do not know" when context is missing.
- Show retrieved sources in the UI.
- Avoid sending unsupported business rules directly in the system prompt.

Improve response quality:

- Add examples to the prompt.
- Ask the LLM to answer in a support-friendly tone.
- Include escalation instructions for sensitive requests.

Production improvements:

- Add authentication for internal dashboards.
- Store chat logs in a database.
- Add analytics for unanswered questions.
- Add human handoff when confidence is low.

## 10. Deployment On Render

1. Push this project to GitHub.
2. Create a new Render Web Service.
3. Connect the GitHub repository.
4. Use these settings:

```text
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app
```

5. Add environment variables in Render:

```text
LLM_PROVIDER
OPENAI_API_KEY or MISTRAL_API_KEY
OPENAI_MODEL or MISTRAL_MODEL
EMBEDDING_MODEL
CHROMA_DB_DIR
DOCUMENTS_DIR
RETRIEVAL_TOP_K
FLASK_SECRET_KEY
```

6. Run ingestion once after deployment.

For a simple demo, you can ingest locally and commit only the sample documents, then let Render build the vector database on first startup if `AUTO_INGEST_ON_START=true`.

For production, prefer a persistent disk for `data/chroma` so embeddings survive restarts.

## 11. Interview Explanation

You can explain the project like this:

> I built a customer support automation chatbot using Retrieval-Augmented Generation. Instead of asking the LLM to answer from memory, I ingest company documents, split them into chunks, generate Sentence Transformer embeddings, and store them in ChromaDB. When a user asks a question, the system retrieves the most relevant chunks and passes them with the query into a carefully designed prompt. The LLM then generates a grounded answer based only on the retrieved context. I exposed this through a Flask `/chat` API and simple web UI, with environment-based configuration, logging, error handling, and Render deployment support.

## 12. Commands Summary

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python -m src.ingest
python app.py
```
