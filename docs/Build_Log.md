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