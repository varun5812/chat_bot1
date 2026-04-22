# Data Directory

Place internal support documents in `data/raw`.

Supported formats:

- `.txt`
- `.md`
- `.pdf`
- `.csv`

Run ingestion after adding or updating files:

```bash
python -m src.ingest
```

The generated ChromaDB files are stored in `data/chroma` and ignored by Git.
