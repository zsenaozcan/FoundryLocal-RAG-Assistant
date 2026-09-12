# Test Question Set — Local Movie RAG Assistant

Run each question through `python main.py` (or the Streamlit UI) in order.
For each one, note whether it behaved as expected (✅) or not (❌), plus a
short note on what actually happened. Paste the raw terminal output back
for the ones you're unsure about.

---

## A) Content Questions (semantic search)

| # | Question | Expected behavior |
|---|---|---|
| A1 | Who directed Fight Club? | "David Fincher" — verifies the character-name hallucination fix holds |
| A2 | What is the plot of The Godfather? | Coherent plot summary, cites a Godfather source file |
| A3 | Tell me about a movie starring Leonardo DiCaprio. | Retrieves a real DiCaprio movie and describes it accurately |
| A4 | What happens in Inception? | Coherent summary grounded in the retrieved context |
| A5 | Which movie features a great white shark terrorizing a beach town? | Should find Jaws |
| A6 | What is Pulp Fiction about? | Plot summary, cites the correct source |

## B) Year + Genre Recommendations (structured search)

| # | Question | Expected behavior |
|---|---|---|
| B1 | Recommend a comedy movie from 1995. | Console shows the structured-filtering message; real 1995 comedy |
| B2 | Suggest an animated movie. | Genre-only filter, no year |
| B3 | What movies came out in 2010? | Year-only filter, no genre |
| B4 | Is there a good thriller from 2008? | Year + genre combined |
| B5 | Recommend a war movie. | Genre-only filter |

## C) Unanswerable / Out-of-scope (hallucination check)

| # | Question | Expected behavior |
|---|---|---|
| C1 | What is the tallest mountain in the world? | Not a movie question — should say it doesn't know, not answer |
| C2 | Who will direct the next Star Wars film in 2030? | Future event, not in dataset |
| C3 | Tell me about the movie "Quantum Butterfly Rebellion." | Made-up title — should not invent a plot |
| C4 | Recommend a movie from 2050. | Year outside dataset coverage |

## D) Edge Cases

| # | Input | Expected behavior |
|---|---|---|
| D1 | (press Enter with no text) | Should not crash, just re-prompt |
| D2 | film | Single vague word — see how it's handled |
| D3 | Godfther | Misspelled title — check if it still finds The Godfather |
| D4 | A long, rambling question mentioning five unrelated movies at once, written as one run-on sentence | Shouldn't crash; answer quality may degrade, note what happens |

## E) System Behavior Checks

| # | Check | Expected behavior |
|---|---|---|
| E1 | Ask A2 (Godfather plot) twice | Answers should be consistent in substance |
| E2 | Check the source(s) shown for A1-A6 | The listed sources should genuinely match the question |
| E3 | Confirm routing | B-section questions show the structured-search message; A-section questions show retrieved sources instead |

---

## How to report back

A quick table works well:
```
Question # | Result | Notes
A1         | ✅     |
C3         | ✅     |
...
```
Paste this after your run, plus the full terminal log if anything looks off —
that way the final documented results in this file reflect what actually
happened, not a guess.