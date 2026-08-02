# Build Log

A plain-English record of each piece of this project, written as it's built —
useful for interviews, LinkedIn posts, and for future-me re-reading this repo.

---

## Step 1: Professional repo scaffold

**What it is:** Set up the repo's folder structure (`src/ingestion`, `src/embeddings`,
`src/vectorstore`, `src/retrieval`, `src/generation`, `src/utils`), plus
`.gitignore`, `LICENSE`, and `.env.example`.

**Why it matters:** Before writing any logic, a clean structure signals to anyone
reading the repo (recruiter, teammate, future-me) that each concern is separated
and testable on its own — ingestion doesn't need to know how generation works,
and vice versa.

**Plain-English summary:** "I set up the skeleton of the project first, the way
you'd draw the floor plan of a house before laying a single brick."

---

## Step 2: Central settings loader (`src/utils/config.py`)

**What it is:** A single Python file that reads all configuration (API keys,
database URLs, feature flags) from a `.env` file, using `pydantic-settings`.

**Why it matters:** Without this, every module (ingestion, embeddings, retrieval,
generation) would each need its own code to read environment variables, and any
typo or missing key would fail silently in a different place each time. With one
central `Settings` object, every module imports the same `settings` and gets
type-checked, validated configuration.

**Plain-English summary:** "Instead of scattering API keys and settings all over
the code, I built one central control panel that every other part of the app
reads from — like a fuse box for the whole house instead of separate wiring
in every room."

---
## Step 3: Document ingestion (`src/ingestion/loader.py`)

**What it is:** Reads `.txt` and `.pdf` files from a folder and splits each one
into overlapping ~1000-character chunks.

**Why it matters:** Language models and vector search work on small, focused
pieces of text, not entire documents. Splitting into chunks with overlap means
a sentence isn't cut in half at a chunk boundary — the last bit of one chunk
reappears at the start of the next, so no context is lost.

**Plain-English summary:** "I built the part that takes a whole document and
cuts it into small, slightly-overlapping pieces — like tearing a long letter
into index cards, but making sure each card includes a bit of the previous
card's last sentence so nothing gets lost."
## Step 4: Embeddings (`src/embeddings/embedder.py`)

**What it is:** Converts text chunks into embedding vectors — lists of 1024
numbers that capture the meaning of the text. Uses Jina AI's API as the
primary provider, with a local model (mxbai-embed-large-v1) as an automatic
fallback when no Jina API key is configured.

**Why it matters:** Vector search (used in the next step) can't compare raw
text directly — it compares these numeric vectors instead, because similar
meanings produce similar vectors even when the wording is completely
different. The local fallback means development can continue without
needing to sign up for a paid API first.

**Plain-English summary:** "I built the part that turns each chunk of text
into a list of 1024 numbers — a kind of fingerprint of its meaning. Two
chunks about similar topics end up with similar fingerprints, even if they
don't share a single word in common. That's what makes 'search by meaning'
possible instead of just keyword matching."
## Step 5: Vector store (`src/vectorstore/store.py`)

**What it is:** Connects to a Qdrant Cloud collection, stores chunks alongside
their embeddings, and searches for the most similar stored chunks given a
query vector.

**Why it matters:** A regular database can't search "by meaning" — it can
only match exact values. Qdrant is built specifically to store vectors and
find the nearest ones to a given query vector extremely fast, even across
millions of entries. This is the engine that makes "search by meaning"
practically possible at scale.

**Plain-English summary:** "I connected the embeddings to a specialized
search database built for comparing meaning instead of exact text. I tested
it by asking it to find the chunk most similar to itself — it correctly
returned a perfect match, proving the whole pipeline (load → chunk → embed →
store → search) works end-to-end."
## Step 6: Retrieval (`src/retrieval/retriever.py`)

**What it is:** A single function, `retrieve(question)`, that takes a plain
English question, embeds it, searches Qdrant, and returns the most relevant
stored chunks — plus a helper that formats those chunks into one text block
ready to hand to an LLM.

**Why it matters:** This is the piece that connects "a user typed a question"
to "here's the relevant information from the knowledge base." Everything
before this (ingestion, embeddings, vector store) exists to make this one
function possible. The next step (generation) will call this directly.

**Plain-English summary:** "I built the actual search function: type a
question, and it finds the most relevant paragraphs from the documents,
ranked by how closely they match. I tested it by asking about the three
stages of a RAG pipeline, and it correctly pulled the exact paragraph from
my sample document that explains that."
## Step 7: Guardrails — rule-based layer (`src/guardrails/rules.py`)

**What it is:** Fast, pattern-based checks that run on every question before
it reaches retrieval or any LLM call — rejecting empty input, excessively
long input, and known prompt-injection phrasing (e.g. "ignore previous
instructions").

**Why it matters:** Not every safety check needs an AI model. Catching
obvious bad input with simple rules is instant and free, and stops junk
requests before they ever cost an API call or reach the more expensive,
LLM-based guardrail layer (added in the next step). This is standard
practice: cheap checks first, expensive checks second.

**Plain-English summary:** "Before any question reaches the AI, it passes
through a quick bouncer that checks for obviously bad input — empty
messages, absurdly long text, or attempts to trick the system into ignoring
its own rules. It's like a metal detector at the door: fast, simple, and it
catches the obvious problems before anyone gets further inside."
## Step 8: LLM Gateway (`src/gateway/llm.py`)

**What it is:** Routes chat completion requests through Portkey to Groq's
Llama 3.3 70B model, using a Portkey virtual key so the real Groq API key
never appears in the codebase.

**Why it matters:** A gateway sits between your app and the actual LLM
provider, giving you centralized observability, the ability to swap
providers (OpenAI, Groq, Anthropic) via a config change instead of a code
change, and automatic fallback if one provider goes down or hits a quota
limit — all without touching application code.

**Plain-English summary:** "I connected the app to an actual AI model, but
through a routing layer instead of directly. That means if I ever want to
switch from Groq to OpenAI, or add a backup provider in case one goes down,
it's a settings change, not a rewrite. I tested it by giving it context
about RAG pipeline stages and asking a question — it answered correctly
using only that context, not its own general knowledge."
## Step 9: Full pipeline wired to the API (`src/generation/generator.py`, `src/app.py`)

**What it is:** `answer_question()` orchestrates the entire pipeline in
order — guardrails check, then retrieval, then generation — and returns a
structured result. The FastAPI `/query` endpoint exposes this over HTTP.

**Why it matters:** This is the point where every previous piece (ingestion,
embeddings, vector store, retrieval, guardrails, LLM gateway) stops being an
isolated, individually-tested module and becomes one working system that
answers real questions through a real API call.

**Plain-English summary:** "This is the moment the project became a real,
working application instead of separate pieces. I can send a question to
my API over HTTP, and it checks the question is safe, searches my documents
for relevant information, and generates an answer using only that
information — citing exactly which document it came from. Tested end-to-end
with curl: sent a question, got back a correct, sourced answer as JSON."
## Step 10: Reranking (`src/retrieval/reranker.py`)

**What it is:** Takes the chunks already found by vector search and re-scores
them against the question using Jina's dedicated Reranker model, which is
more precise than embedding similarity alone.

**Why it matters:** Vector similarity search is fast but approximate — it's
good at finding "roughly relevant" candidates quickly across large datasets,
but not always great at fine-grained ranking. Reranking adds a second,
slower-but-more-accurate pass on just the top candidates, sharpening exactly
which ones are truly most relevant before they go to the LLM.

**Plain-English summary:** "I added a second, more careful pass after the
initial search — like getting a shortlist of candidates fast, then having
an expert carefully rank just that shortlist. Testing it showed the
reranker gave a much clearer, more confident distinction between the
relevant and less relevant chunk than the original search score did."
## Step 11: Multi-format ingestion (`src/ingestion/loader.py`)

**What it is:** Extended the ingestion module to support `.docx`, `.pptx`,
and `.html` files, in addition to the original `.txt` and `.pdf`. Uses a
dictionary mapping file extensions to their specific parsing function, and
skips unsupported or corrupted files gracefully instead of crashing the
whole batch.

**Why it matters:** Real-world knowledge bases are rarely just plain text —
they're a mix of Word docs, slide decks, PDFs, and web pages. Supporting
multiple formats means the system can ingest a realistic company knowledge
base, not just a toy dataset.

**Plain-English summary:** "I expanded the ingestion step to understand
five different file types instead of two,