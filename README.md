# Qanoun AI

[![CI](https://github.com/Haytamzerr/qanounAI/actions/workflows/ci.yml/badge.svg)](https://github.com/Haytamzerr/qanounAI/actions/workflows/ci.yml)
![Status](https://img.shields.io/badge/status-work%20in%20progress-B08D57)
![License](https://img.shields.io/badge/license-MIT-0B6E4F)

**Ask a question about Moroccan law in Darija, Arabic or French, and get a fast answer that cites the exact articles it relies on.**

> Qanoun AI provides general legal information, not legal advice. The Arabic text published in the
> Bulletin officiel is the official version of Moroccan law; French texts are translations.

## Why

Legal texts are public but hard to use: long PDFs, legal vocabulary, two official languages, and no
help for people who think and speak in Darija. Qanoun AI closes that gap while staying honest: every
claim is tied to an article, and every citation is verified before it is shown.

## Planned features

- Questions in **Darija** (Arabic script and Arabizi), **Modern Standard Arabic** and **French**
- Retrieval-augmented answers with **verified article citations** and refusals when the law isn't covered
- **Hybrid search** (dense + sparse) with re-ranking over a curated corpus of Moroccan laws
- An open **Darija legal lexicon** mapping everyday words to legal terms
- A tool-calling **agent** for multi-step questions, and an **MCP server** exposing the legal tools
- An **evaluation suite** (retrieval, faithfulness, citation validity, Darija fidelity)
- A streaming, bilingual (RTL/LTR) web interface targeting about one second to first words

## Project layout

```text
src/qanoun/
├── ingestion/    # PDFs → clean text → one record per article
├── retrieval/    # embeddings, hybrid search, re-ranking, cache
├── generation/   # question understanding (Darija), answers, citation checks
├── agent/        # tools and agent loop
├── mcp_server/   # MCP server
└── api/          # FastAPI service
data/             # raw / interim / processed (not committed)
eval/             # gold questions, evaluation scripts, reports
docs/             # architecture and design decisions
tests/
```

## Quick start (development)

Requires [uv](https://docs.astral.sh/uv/) and Python 3.12.

```bash
git clone https://github.com/Haytamzerr/qanounAI.git
cd qanounAI
uv sync                        # create the environment and install dependencies
uv run pre-commit install      # check code style on every commit
cp .env.example .env           # then fill in your own values
uv run pytest                  # run the fast tests
uv run pytest -m slow          # also run the tests on the real law PDFs (about 1 min)
```

## Build the legal corpus

```bash
uv run python -m qanoun.ingestion.build
```

Reads the PDFs listed in `data/sources.csv` from `data/raw/`, writes one JSON record per article to
`data/processed/articles.jsonl`, and fails if a quality check does not pass. See
[docs/corpus.md](docs/corpus.md) for the sources and how the parser reads them.

## Index the articles for meaning-based search

Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/) running.

```bash
docker compose up -d qdrant                 # start the vector database (Qdrant)
uv run python -m qanoun.retrieval.index     # embed the 1,329 articles with BGE-M3 and load them
```

The first run downloads the BGE-M3 model (about 2.3 GB) and embeds every article on the CPU, which
takes several minutes. The vectors are saved in `data/processed/embeddings/` and reused until an
article or the model changes. The Qdrant dashboard is at http://localhost:6333/dashboard.

Without Docker (in a cloud notebook, or on a PC short of memory), set `QANOUN_QDRANT_URL=data/qdrant`:
Qdrant then runs inside Python and saves to that folder.

## Evaluate search

```bash
uv run python -m qanoun.retrieval.evaluate --method bm25 dense hybrid
```

Scores each search method on 45 test questions (`eval/retrieval_set.jsonl`) in Arabic, French and Darija, writes one report per method to `eval/reports/`, and a comparison table when several methods run.

| Method | Hit@5 | Arabic | French | Darija (Arabic script) | Arabizi |
| --- | --- | --- | --- | --- | --- |
| BM25 keywords (baseline) | 47% | 78% | 11% | 25% | 11% |
| **Dense (BGE-M3 + Qdrant)** | **82%** | **100%** | **100%** | **75%** | 22% |
| Hybrid (BM25 + dense, RRF) | 73% | 96% | 89% | 25% | 22% |

Meaning-based search finds the right article for every Arabic and French question, including French
questions answered by Arabic-only laws. Plain RRF fusion *lowers* the score: BM25 can't match across
languages, so it pushes wrong articles into the fused list. Arabizi (Darija in Latin letters) is the
open problem: the next step converts it to Arabic script before searching.

## Roadmap

- [x] Phase 0: project setup
- [x] Phase 1: legal corpus: 1,329 articles from 5 texts: personal data (09-08, Arabic + French), Labour Code (65.99, July 2026), Family Code (70.03), Consumer Protection (31.08)
- [ ] Phase 2: indexing and hybrid retrieval
- [ ] Phase 3: grounded answers with citations
- [ ] Phase 4: evaluation framework
- [ ] Phase 5: agent and MCP server
- [ ] Phase 6: API, interface, Docker, deployment
- [ ] Phase 7: safety
- [ ] Phase 8: demo and write-up

## License

MIT
