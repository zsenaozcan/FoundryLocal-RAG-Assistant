"""
Bulk ingestion: embeds every chunk produced by chunking.py and stores it
in SQLite.

Designed to be RESUMABLE: this run can take hours for a large dataset
(e.g. all 45,000 movies), so if it gets interrupted (laptop sleeps,
error, you close the terminal), re-running this script picks up where
it left off instead of starting from zero.

How resuming works:
  1. Before starting, we read which (source, chunk_index) pairs are
     already in the database.
  2. We skip embedding any chunk that's already there - this is the
     expensive part (calling the model), so skipping it is what makes
     resuming actually fast.
  3. We commit to the database every BATCH_COMMIT_EVERY rows, not just
     once at the very end, so a crash loses at most a small batch of
     work instead of everything.
"""

import json
import time

from chunking import process_docs_folder
from foundry_manager import get_embedding
from database import get_connection

BATCH_COMMIT_EVERY = 50
PROGRESS_EVERY = 200


def get_already_ingested(conn):
    """Returns a set of (source, chunk_index) tuples already saved in the
    database, so we know what to skip on a resumed run."""
    cursor = conn.cursor()
    cursor.execute("SELECT source, chunk_index FROM documents")
    return set(cursor.fetchall())


def run_bulk_ingestion():
    print("Reading and chunking all files in docs/ ...")
    chunks = process_docs_folder()
    total = len(chunks)
    print(f"Found {total} chunks total.\n")

    with get_connection() as conn:
        already_done = get_already_ingested(conn)
        print(f"{len(already_done)} chunks are already in the database - these will be skipped.\n")

        cursor = conn.cursor()
        pending_commits = 0
        newly_added = 0
        errors = 0
        start_time = time.time()

        for i, chunk in enumerate(chunks, start=1):
            key = (chunk["source"], chunk["chunk_index"])

            if key in already_done:
                continue

            try:
                vector = get_embedding(chunk["content"])
            except Exception as e:
                # Don't let one bad chunk kill an hours-long run - log it
                # and keep going. Since it wasn't inserted, it will be
                # retried automatically the next time you run this script.
                print(f"  ERROR embedding {chunk['source']} #{chunk['chunk_index']}: {e}")
                errors += 1
                continue

            vector_str = json.dumps(vector)

            # INSERT OR IGNORE: extra safety net against the UNIQUE
            # constraint, in case the same chunk somehow gets processed twice
            cursor.execute(
                """
                INSERT OR IGNORE INTO documents (source, chunk_index, content, embedding)
                VALUES (?, ?, ?, ?)
                """,
                (chunk["source"], chunk["chunk_index"], chunk["content"], vector_str)
            )

            newly_added += 1
            pending_commits += 1

            if pending_commits >= BATCH_COMMIT_EVERY:
                conn.commit()
                pending_commits = 0

            if i % PROGRESS_EVERY == 0 or i == total:
                elapsed = time.time() - start_time
                rate = newly_added / elapsed if elapsed > 0 else 0
                remaining = total - i
                eta_seconds = remaining / rate if rate > 0 else 0
                print(
                    f"  {i}/{total} scanned | {newly_added} newly embedded | "
                    f"{elapsed:.0f}s elapsed | ETA ~{eta_seconds / 60:.0f} min"
                )

        conn.commit()  # final commit for any rows since the last checkpoint

    print(f"\nDone. {newly_added} new chunks embedded and saved. {errors} errors skipped.")
    if errors > 0:
        print("Re-run this script to retry the chunks that had errors.")


if __name__ == "__main__":
    run_bulk_ingestion()