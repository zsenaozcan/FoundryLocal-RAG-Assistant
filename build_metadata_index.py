"""
Adds a structured 'movies_metadata' table to the database, parsed from the
same source data used to build docs/*.txt.

This does NOT touch or recompute any embeddings - it just adds a parallel
structured index (title, year, genres, director) that supports exact
filtering and sorting, which pure vector similarity search cannot do
reliably (e.g. "the most recent film by a specific director", or
"all action movies released in 2000").

Requires the same ./data/ CSVs used by prepare_movies_data.py.
"""

import pandas as pd

from prepare_movies_data import load_and_merge, extract_director, extract_top_names, slugify
from database import get_connection


def create_metadata_table(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movies_metadata (
            source TEXT PRIMARY KEY,
            title TEXT,
            year INTEGER,
            genres TEXT,
            director TEXT,
            vote_count INTEGER
        )
    ''')
    conn.commit()


def build_index():
    print("Loading and merging source CSVs...")
    df = load_and_merge()
    df = df[df["overview"].notna() & (df["overview"].str.strip() != "")]
    df["vote_count"] = pd.to_numeric(df["vote_count"], errors="coerce").fillna(0).astype(int)

    with get_connection() as conn:
        create_metadata_table(conn)
        cursor = conn.cursor()

        written = 0
        for _, row in df.iterrows():
            title = row.get("title") or "Unknown Title"

            release_date = row.get("release_date")
            year = None
            if pd.notna(release_date) and len(str(release_date)) >= 4:
                try:
                    year = int(str(release_date)[:4])
                except ValueError:
                    year = None

            genres = ", ".join(extract_top_names(row.get("genres"), limit=10))
            director = extract_director(row.get("crew"))
            source = f"{int(row['id'])}_{slugify(str(title))}.txt"
            vote_count = int(row.get("vote_count", 0))

            cursor.execute(
                """
                INSERT OR REPLACE INTO movies_metadata (source, title, year, genres, director, vote_count)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (source, title, year, genres, director, vote_count)
            )
            written += 1

            if written % 5000 == 0:
                print(f"  {written} rows indexed...")

        conn.commit()

    print(f"\nDone. Metadata index built for {written} movies.")


if __name__ == "__main__":
    build_index()