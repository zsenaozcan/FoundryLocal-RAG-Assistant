"""
Lightweight structured search layer, used to answer year/genre filtered
recommendation questions that pure vector similarity search can't handle
reliably (e.g. "recommend an action movie from 2000"). Vector search finds
text that reads similarly to the query, but doesn't guarantee an
exhaustive or exact match on structured facts like a release year.

This is heuristic (regex/keyword based), not a full language parser - if
it doesn't recognize a year or genre in the question, answer_query() in
assistant.py falls back to the normal semantic RAG pipeline.
"""

import re

from database import get_connection
from foundry_manager import get_chat_client

# keyword -> the genre value as it actually appears in movies_metadata.genres
GENRE_KEYWORDS = {
    "action": "Action",
    "comedy": "Comedy",
    "drama": "Drama",
    "horror": "Horror",
    "thriller": "Thriller",
    "romance": "Romance",
    "science fiction": "Science Fiction", "sci-fi": "Science Fiction",
    "animation": "Animation",
    "adventure": "Adventure",
    "crime": "Crime",
    "fantasy": "Fantasy",
    "mystery": "Mystery",
    "war": "War",
    "western": "Western",
    "documentary": "Documentary",
    "family": "Family",
    "music": "Music",
    "history": "History",
}


def extract_year(question):
    match = re.search(r"\b(19|20)\d{2}\b", question)
    return int(match.group()) if match else None


def extract_genre(question):
    q_lower = question.lower()
    for keyword, genre_value in GENRE_KEYWORDS.items():
        if keyword in q_lower:
            return genre_value
    return None


def find_by_filters(year=None, genre=None, limit=8):
    """Returns up to `limit` movies matching the given filters, ranked by
    vote_count so well-known movies are suggested before obscure ones."""
    query = "SELECT title, year, genres, director FROM movies_metadata WHERE 1=1"
    params = []
    if year:
        query += " AND year = ?"
        params.append(year)
    if genre:
        query += " AND genres LIKE ?"
        params.append(f"%{genre}%")
    query += " ORDER BY vote_count DESC LIMIT ?"
    params.append(limit)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()


def try_structured_answer(question):
    """Attempts to answer using exact year/genre filtering.
    Returns an answer string, or None if no year/genre was found in the
    question (caller should fall back to semantic search)."""
    year = extract_year(question)
    genre = extract_genre(question)

    if not year and not genre:
        return None

    rows = find_by_filters(year=year, genre=genre)
    if not rows:
        return None

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
                "more movies from the candidate list that best match the "
                "user's request, and briefly explain why, using ONLY the "
                "title, year, genres, and director shown for each "
                "candidate. Do not invent other movies. "
                "CRITICAL RULE: the candidate list contains NO actor "
                "names, character names, or plot details. If you mention "
                "any actor, character, or plot detail, you are making it "
                "up - this is strictly forbidden. Base your explanation "
                "only on genre, year, and director. "
                "Always respond in English, regardless of what language "
                "the request was written in. Keep your answer concise - "
                "2 to 4 sentences."
            ),
        },
        {
            "role": "user",
            "content": f"Candidates:\n{candidates}\n\nRequest: {question}",
        },
    ])
    return response.choices[0].message.content