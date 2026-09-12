# Offline Movie RAG Assistant

A fully offline Retrieval-Augmented Generation (RAG) assistant that answers
questions about movies using [The Movies Dataset](https://www.kaggle.com/datasets/rounakbanik/the-movies-dataset)
(~44,600 movies), powered by [Microsoft Foundry Local](https://learn.microsoft.com/azure/ai-foundry/foundry-local/)
for on-device embedding and chat inference, with SQLite as the local vector
store.

No cloud API calls are made at runtime — embeddings, retrieval, and answer
generation all run entirely on the local machine.

## Features

- Semantic search over movie plots, cast, and crew using local embeddings (`qwen3-embedding-0.6b`)
- Structured year/genre filtering for recommendation-style questions (e.g.
  "recommend an action movie from 2000"), ranked by popularity
- A local chat model (`qwen2.5-0.5b`) generates grounded answers and is
  instructed to say "I don't know" when the context is insufficient
- Fully resumable bulk ingestion — safe to interrupt and resume a
  multi-hour embedding run without losing progress or redoing work

## Architecture

```
Kaggle CSVs --> prepare_movies_data.py --> docs/*.txt
                                                |
                                          chunking.py
                                                |
                          ingest_bulk.py --(embeddings)--> SQLite: documents table
                                                |
                    build_metadata_index.py --(structured fields)--> SQLite: movies_metadata table

User question --> assistant.py --routes to--> structured_query.py (year/genre)
                                    or
                                   search.py (semantic)
                                          |
                              foundry_manager.py (local chat model)
                                          |
                                       Answer
```

## Prerequisites

- Python 3.10+
- [Microsoft Foundry Local](https://learn.microsoft.com/azure/ai-foundry/foundry-local/) installed
- A Kaggle account (only needed once, to download the dataset)

## Setup

**1. Create a virtual environment and install dependencies**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**2. Download the dataset**
```powershell
pip install kaggle
kaggle datasets download -d rounakbanik/the-movies-dataset --unzip -p data
```

**3. Build the knowledge base** (one-time setup; `ingest_bulk.py` is long-running but resumable)
```powershell
python prepare_movies_data.py     # Kaggle CSVs -> docs/*.txt
python database.py                # create the SQLite schema
python ingest_bulk.py             # embed all chunks (can take several hours - safe to Ctrl+C and re-run)
python build_metadata_index.py    # build the structured year/genre/director index
```

**4. Run the assistant**
```powershell
python main.py
```

## Usage

Ask questions directly at the prompt:
```
Ask a question about a movie: What is the plot of Fight Club?
Ask a question about a movie: Recommend an action movie from 2000
```
Type `exit` to quit. See `test_questions.md` for a broader set of example
questions and expected behavior.

## Project structure

| File | Purpose |
|---|---|
| `prepare_movies_data.py` | Converts Kaggle CSVs into per-movie `.txt` files in `docs/` |
| `chunking.py` | Splits `.txt` files into embeddable chunks |
| `foundry_manager.py` | Singleton manager for Foundry Local (embedding + chat clients loaded once) |
| `database.py` | SQLite schema and connection helper |
| `ingest_bulk.py` | Resumable bulk embedding of all chunks into SQLite |
| `ingest.py` | Utility to embed and store a single ad-hoc document |
| `search.py` | Semantic (vector similarity) search over embedded chunks |
| `build_metadata_index.py` | Builds the structured `movies_metadata` table (title/year/genres/director/vote_count) |
| `structured_query.py` | Year/genre filtered recommendation logic |
| `assistant.py` | Core RAG pipeline: routes a question to structured or semantic search, then queries the local chat model |
| `main.py` | CLI entry point |
| `test_questions.md` | Test question checklist used for functional evaluation |

## Known limitations

- The dataset reflects a fixed Kaggle snapshot of TMDb data, not real-time
  information — recommendations only draw from movies included in that
  snapshot.
- Year/genre detection in `structured_query.py` is keyword/regex-based, not
  a full language parser; unusual phrasing may fall back to semantic search
  instead of exact filtering. Only English keywords are recognized, matching
  the dataset's language.
- Designed for single-user, local/offline use — not built for concurrent
  access or production deployment.
- Some movies share an identical title (e.g. multiple entries named
  "Titanic"), which can cause semantic search to surface a different film
  than the one intended.
- Even with prompt constraints and a similarity-confidence threshold, the
  small local chat model (`qwen2.5-1.5b`) can still occasionally state
  incidental details not present in the retrieved context. The threshold
  reduces this significantly but does not eliminate it entirely.

## Data source

Movie data: [The Movies Dataset](https://www.kaggle.com/datasets/rounakbanik/the-movies-dataset)
by Rounak Banik on Kaggle (sourced from TMDb and GroupLens).