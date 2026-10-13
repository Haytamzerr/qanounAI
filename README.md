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
uv run pytest                  # run the tests
```

## Build the legal corpus

```bash
uv run python -m qanoun.ingestion.build
```

Reads the PDFs listed in `data/sources.csv` from `data/raw/`, writes one JSON record per article to
`data/processed/articles.jsonl`, and fails if a quality check does not pass. See
[docs/corpus.md](docs/corpus.md) for the sources and how the parser reads them.

## Roadmap

- [x] Phase 0: project setup
- [ ] Phase 1: legal corpus (article-level dataset): Law 09-08 in French done (67 articles)
- [ ] Phase 2: indexing and hybrid retrieval
- [ ] Phase 3: grounded answers with citations
- [ ] Phase 4: evaluation framework
- [ ] Phase 5: agent and MCP server
- [ ] Phase 6: API, interface, Docker, deployment
- [ ] Phase 7: safety
- [ ] Phase 8: demo and write-up

## License

MIT
