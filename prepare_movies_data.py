"""
Step: Convert "The Movies Dataset" (Kaggle) into per-movie .txt documents
inside docs/, so the existing chunking.py -> ingest.py pipeline can
process them without any changes.

Source: https://www.kaggle.com/datasets/rounakbanik/the-movies-dataset

Expected input files under ./data/:
  - movies_metadata.csv   (required: title, overview, genres, release_date...)
  - credits.csv           (required: cast, crew - stringified Python lists)
  - keywords.csv          (optional: keywords - stringified Python list)

Requires pandas: pip install pandas
"""

import ast
import os
import re

import pandas as pd

DATA_FOLDER = "data"
DOCS_FOLDER = "docs"
TOP_N_MOVIES = None  # set to an integer (e.g. 300) to sample only the most
                      # popular movies; None processes the entire dataset
REQUIRE_OVERVIEW = True  # skip movies with no overview text - they would
                          # produce empty, useless documents for the RAG pipeline


def safe_literal_eval(value):
    """Kaggle's stringified JSON-like columns (genres, cast, crew, keywords)
    need ast.literal_eval to become real Python lists/dicts. Falls back to
    an empty list on malformed rows (this dataset has a few known ones)."""
    try:
        return ast.literal_eval(value) if isinstance(value, str) else []
    except (ValueError, SyntaxError):
        return []


def slugify(text):
    """Turns a movie title into a safe filename fragment."""
    text = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()
    return text[:50] if text else "untitled"


def load_and_merge(data_folder=DATA_FOLDER):
    print("Loading movies_metadata.csv...")
    metadata = pd.read_csv(
        os.path.join(data_folder, "movies_metadata.csv"),
        low_memory=False
    )

    # A handful of rows in this dataset have a corrupted 'id' column
    # (known issue with this Kaggle dataset) - filter those out
    metadata = metadata[metadata["id"].apply(lambda x: str(x).isdigit())].copy()
    metadata["id"] = metadata["id"].astype(int)

    print("Loading credits.csv...")
    credits = pd.read_csv(os.path.join(data_folder, "credits.csv"))
    credits["id"] = credits["id"].astype(int)

    keywords = None
    keywords_path = os.path.join(data_folder, "keywords.csv")
    if os.path.exists(keywords_path):
        print("Loading keywords.csv...")
        keywords = pd.read_csv(keywords_path)
        keywords["id"] = keywords["id"].astype(int)

    merged = metadata.merge(credits, on="id", how="left")
    if keywords is not None:
        merged = merged.merge(keywords, on="id", how="left")

    return merged


def extract_director(crew_str):
    crew = safe_literal_eval(crew_str)
    for member in crew:
        if member.get("job") == "Director":
            return member.get("name")
    return "Unknown"


def extract_top_names(list_str, limit=5):
    items = safe_literal_eval(list_str)
    return [item.get("name") for item in items[:limit] if item.get("name")]


def build_document_text(row, has_keywords):
    """Builds a single plain-text block describing one movie."""
    title = row.get("title") or "Unknown Title"
    release_date = row.get("release_date")
    year = str(release_date)[:4] if pd.notna(release_date) else "Unknown"
    genres = ", ".join(extract_top_names(row.get("genres"), limit=10)) or "Unknown"
    overview = row.get("overview") if pd.notna(row.get("overview")) else "No overview available."
    director = extract_director(row.get("crew"))
    cast = ", ".join(extract_top_names(row.get("cast"), limit=5)) or "Unknown"

    lines = [
        f"Title: {title} ({year})",
        f"Genres: {genres}",
        f"Director: {director}",
        f"Main Cast: {cast}",
    ]

    if has_keywords:
        keywords = ", ".join(extract_top_names(row.get("keywords"), limit=10))
        if keywords:
            lines.append(f"Keywords: {keywords}")

    lines.append("")
    lines.append(f"Overview: {overview}")

    return "\n".join(lines)


def export_to_docs(top_n=TOP_N_MOVIES, docs_folder=DOCS_FOLDER,
                    require_overview=REQUIRE_OVERVIEW):
    df = load_and_merge()
    has_keywords = "keywords" in df.columns

    if require_overview:
        before = len(df)
        df = df[df["overview"].notna() & (df["overview"].str.strip() != "")]
        print(f"Dropped {before - len(df)} movies with no overview text.")

    df["vote_count"] = pd.to_numeric(df["vote_count"], errors="coerce").fillna(0)

    if top_n is not None:
        # Rank by vote_count so we keep well-known movies with meaningful
        # data, instead of a random slice full of obscure entries
        df = df.sort_values("vote_count", ascending=False).head(top_n)

    total = len(df)
    print(f"Preparing to write {total} movie documents...")

    os.makedirs(docs_folder, exist_ok=True)

    written = 0
    for _, row in df.iterrows():
        text = build_document_text(row, has_keywords)
        filename = f"{int(row['id'])}_{slugify(str(row.get('title', 'untitled')))}.txt"
        filepath = os.path.join(docs_folder, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)
        written += 1

        # Progress logging - useful since this can be a large batch
        if written % 2000 == 0 or written == total:
            print(f"  {written}/{total} documents written...")

    print(f"\nDone. {written} movie documents written to '{docs_folder}/'.")


if __name__ == "__main__":
    export_to_docs()