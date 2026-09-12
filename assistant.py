"""
Step: Connect retrieval (search.py) to the local chat model (Foundry Local)
to produce grounded answers. This closes the Retrieve -> Augment ->
Generate loop that defines RAG.
"""

from search import search_database
from foundry_manager import get_chat_client
from structured_query import try_structured_answer

TOP_K = 3
MIN_SIMILARITY = 0.58  # recalibrated after adding the query instruction
                        # prefix to search.py: good matches now score
                        # ~0.61-0.67, irrelevant questions ~0.48-0.49.
                        # Keep adjusting as you gather more test data.

SYSTEM_PROMPT = (
    "You are a movie knowledge assistant. Answer the user's question using "
    "ONLY the movie information provided in the context below. "
    "Do not mention any actor, director, date, or plot detail that is not "
    "explicitly written in the context - if you are not certain a fact "
    "appears in the context, leave it out rather than guessing. "
    "The context only lists actor NAMES, not character/role names - never "
    "state which character an actor plays, since that information was not "
    "given to you. "
    "Always mention the title(s) of the movie(s) you used to answer. "
    "If the context does not contain enough information to answer the "
    "question, say clearly that you don't know based on the available data. "
    "Always respond in English, regardless of what language the question "
    "was asked in. Keep your answer concise - 2 to 4 sentences. "
    "Do not use any knowledge outside of the provided context."
)


def build_context(results):
    """Formats retrieved (score, content, source) tuples into a single
    context block for the prompt."""
    blocks = []
    for score, content, source in results:
        blocks.append(f"[Source: {source}]\n{content}")
    return "\n\n---\n\n".join(blocks)


def answer_query(question, top_k=TOP_K, show_retrieved=True):
    """Runs the full RAG pipeline: retrieve relevant chunks, then ask the
    local chat model to answer using them as context.

    First tries structured (exact filter) answering for question types
    vector search handles poorly - e.g. a director's most recent film, or
    a year+genre filtered recommendation. Falls back to semantic search
    for everything else."""
    structured = try_structured_answer(question)
    if structured:
        if show_retrieved:
            print("\n(Answered using structured metadata filtering, not semantic search)\n")
        return structured

    results = search_database(question, top_k=top_k)

    if not results or results[0][0] < MIN_SIMILARITY:
        if show_retrieved:
            print(f"\n(Best match score {results[0][0]:.4f} is below the "
                  f"confidence threshold {MIN_SIMILARITY} - skipping the "
                  f"model to avoid an unreliable answer.)\n")
        return (
            "I don't have reliable information about this in my movie "
            "database - the closest matches weren't a good fit. This "
            "movie may not be in my dataset, or try rephrasing the question."
        )

    if show_retrieved:
        print("\n--- Retrieved context ---")
        for score, content, source in results:
            print(f"  [{score:.4f}] {source}")
        print("-------------------------\n")

    context = build_context(results)
    user_message = f"Context:\n{context}\n\nQuestion: {question}"

    client = get_chat_client()
    response = client.complete_chat([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ])

    return response.choices[0].message.content