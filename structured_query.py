"""
Lightweight structured search layer, used to answer question types that
pure vector similarity search cannot reliably handle:

  - "What is <director>'s most recent movie?"  -> exact filter + sort
  - "Recommend an action movie from 2000."      -> exact filter

Vector search finds text that reads similarly to the query, but it does
not guarantee an EXHAUSTIVE or EXACT match on structured facts like a
release year or a director's full filmography - it can miss the right
movie, or confidently return the wrong one. For these question types we
query the movies_metadata table directly instead.

This is heuristic (regex/keyword based), not a full language parser - if
it doesn't recognize the pattern, answer_query() falls back to the normal
semantic RAG pipeline in assistant.py.

Note: "most recent" is relative to this dataset's coverage (The Movies
Dataset), which has its own cutoff date - it will not reflect a
director's real-world latest release if it's newer than the dataset.
"""

import re

from database import get_connection
from foundry_manager import get_chat_client

RECENCY_KEYWORDS = [
    "latest", "most recent", "newest", "last movie", "recent film",
    "son filmi", "en son", "en yeni",
]

# keyword -> the genre value as it actually appears in movies_metadata.genres
GENRE_KEYWORDS = {
    "action": "Action", "aksiyon": "Action",
    "comedy": "Comedy", "komedi": "Comedy",
    "drama": "Drama", "dram": "Drama",
    "horror": "Horror", "korku": "Horror",
    "thriller": "Thriller", "gerilim": "Thriller",
    "romance": "Romance", "romantik": "Romance",
    "science fiction": "Science Fiction", "sci-fi": "Science Fiction", "bilim kurgu": "Science Fiction",
    "animation": "Animation", "animasyon": "Animation",
    "adventure": "Adventure", "macera": "Adventure",
    "crime": "Crime", "suç": "Crime",
    "fantasy": "Fantasy", "fantastik": "Fantasy",
    "mystery": "Mystery", "gizem": "Mystery",
    "war": "War", "savaş": "War",
    "western": "Western",
    "documentary": "Documentary", "belgesel": "Documentary",
    "family": "Family", "aile": "Family",
    "music": "Music", "müzik": "Music",
    "history": "History", "tarih": "History",
}


def extract_probable_name(question):
    """Grabs a run of 2+ consecutive capitalized words as the most likely
    proper-noun mention in the question (e.g. a director's name).
    Strips trailing possessive suffixes in any language (Michael Haneke'nin
    -> Michael Haneke, Spielberg's -> Spielberg)."""
    words = question.split()
    candidates = []
    current = []

    for w in words:
        stripped = w.strip(",.?!\"'")
        clean = re.sub(r"['’`].*$", "", stripped)
        if clean[:1].isupper() and len(clean) > 1:
            current.append(clean)
        else:
            if len(current) >= 2:
                candidates.append(" ".join(current))
            current = []

    if len(current) >= 2:
        candidates.append(" ".join(current))

    return candidates[0] if candidates else None


def extract_year(question):
    match = re.search(r"\b(19|20)\d{2}\b", question)
    return int(match.group()) if match else None


def extract_genre(question):
    q_lower = question.lower()
    for keyword, genre_value in GENRE_KEYWORDS.items():
        if keyword in q_lower:
            return genre_value
    return None


def find_latest_by_director(name):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT title, year FROM movies_metadata
            WHERE director LIKE ? AND year IS NOT NULL
            ORDER BY year DESC
            LIMIT 1
            """,
            (f"%{name}%",)
        )
        return cursor.fetchone()


def find_by_filters(year=None, genre=None, limit=8):
    query = "SELECT title, year, genres, director FROM movies_metadata WHERE 1=1"
    params = []
    if year:
        query += " AND year = ?"
        params.append(year)
    if genre:
        query += " AND genres LIKE ?"
        params.append(f"%{genre}%")
    query += " LIMIT ?"
    params.append(limit)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()


def try_structured_answer(question):
    """Attempts to answer using exact metadata filtering.
    Returns an answer string, or None if no structured pattern matched
    (caller should fall back to semantic search)."""

    # Pattern 1: "<Director>'s most recent/latest film"
    if any(keyword in question.lower() for keyword in RECENCY_KEYWORDS):
        name = extract_probable_name(question)
        if name:
            row = find_latest_by_director(name)
            if row:
                title, year = row
                return (
                    f"Based on this dataset, {name}'s most recent movie is "
                    f"\"{title}\" ({year})."
                )

    # Pattern 2: filter by year and/or genre -> recommend from candidates
    year = extract_year(question)
    genre = extract_genre(question)
    if year or genre:
        rows = find_by_filters(year=year, genre=genre)
        if rows:
            candidates = "\n".join(
                f"- {title} ({y}) - Genres: {g} - Director: {d}"
                for title, y, g, d in rows
            )
            client = get_chat_client()
            response = client.complete_chat([
                {
                    "role": "system",
                    "content": (
                        "You are a movie recommendation assistant. Pick one or "
                        "more movies from the candidate list that best match "
                        "the user's request, and briefly explain why. Only use "
                        "the candidates listed - do not invent other movies."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Candidates:\n{candidates}\n\nRequest: {question}",
                },
            ])
            return response.choices[0].message.content

    return None
