"""
Entry point for the offline movie RAG assistant.

Run with: python main.py
"""

from assistant import answer_query


def main():
    print("Local Movie RAG Assistant - type 'exit' to quit.\n")
    while True:
        question = input("Ask a question about a movie: ").strip()
        if question.lower() in ("exit", "quit"):
            break
        if not question:
            continue

        answer = answer_query(question)
        print(f"\nAssistant: {answer}\n")


if __name__ == "__main__":
    main()