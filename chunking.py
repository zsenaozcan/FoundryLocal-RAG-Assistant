"""
Step 1: Read .txt files from the docs/ folder and split them into
meaningful chunks.

This step does NOT include embedding or writing to the database yet; it
only converts raw text into manageable pieces that ingest.py will be
ready to process. Once approved, these chunks will be connected to
ingest.py.
"""

import os

DOCS_FOLDER = "docs"
CHUNK_SIZE = 500       # approximate chunk size, in characters
CHUNK_OVERLAP = 50     # overlap used when splitting very long paragraphs


def load_txt_files(docs_folder=DOCS_FOLDER):
    """Reads all .txt files in the docs/ folder.
    Returns a list of (filename, content) tuples."""
    documents = []

    if not os.path.isdir(docs_folder):
        raise FileNotFoundError(
            f"Folder '{docs_folder}' not found. "
            f"Make sure you created a FOLDER named 'docs' in the project "
            f"root and placed your .txt files inside it."
        )

    for filename in sorted(os.listdir(docs_folder)):
        if filename.lower().endswith(".txt"):
            filepath = os.path.join(docs_folder, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
            if content:
                documents.append((filename, content))
                print(f"Read: {filename} ({len(content)} characters)")
            else:
                print(f"Warning: '{filename}' is empty, skipping.")

    if not documents:
        print(f"Warning: no .txt files found to read in '{docs_folder}'.")

    return documents


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Splits a text into chunks while respecting paragraph boundaries.
    If a single paragraph is larger than chunk_size on its own, it is
    additionally split into overlapping character ranges."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [text]

    chunks = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 1 <= chunk_size:
            current = f"{current}\n{para}".strip()
        else:
            if current:
                chunks.append(current)
            if len(para) > chunk_size:
                start = 0
                while start < len(para):
                    end = start + chunk_size
                    chunks.append(para[start:end])
                    start = end - overlap
                current = ""
            else:
                current = para

    if current:
        chunks.append(current)

    return chunks


def process_docs_folder(docs_folder=DOCS_FOLDER):
    """Reads all .txt files and splits them into chunks.
    Also keeps track of each chunk's source filename.

    Returns: [{"source": filename, "content": chunk_text}, ...]
    """
    all_chunks = []

    for filename, content in load_txt_files(docs_folder):
        chunks = chunk_text(content)
        print(f"'{filename}' -> split into {len(chunks)} chunks.")
        for index, chunk in enumerate(chunks):
            all_chunks.append({
                "source": filename,
                "chunk_index": index,
                "content": chunk,
            })

    print(f"\nTotal: {len(all_chunks)} chunks created.")
    return all_chunks


if __name__ == "__main__":
    chunks = process_docs_folder()

    print("\n--- Sample output (first 2 chunks) ---")
    for c in chunks[:2]:
        print(f"\n[Source: {c['source']}]")
        preview = c["content"][:200]
        print(preview + ("..." if len(c["content"]) > 200 else ""))