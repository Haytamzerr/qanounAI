# Design decisions

A short record of each important choice and why it was made. Recruiters often ask "why did you do
it this way?": this file is the answer.

| # | Date | Decision | Why | Alternatives considered |
| --- | --- | --- | --- | --- |
| 1 | 2026-10-13 | `src/` layout with one subpackage per stage | Tests import the installed package, not loose files; each stage can be tested alone | Flat scripts, notebooks |
| 2 | 2026-10-13 | uv for environments and dependencies | One fast tool, a lock file for reproducible installs | pip + venv, Poetry |
| 3 | 2026-10-13 | Settings from environment variables via pydantic-settings | Secrets never in code; same code runs locally, in CI and in production | Hard-coded constants, config files |
| 4 | 2026-10-13 | Raw, interim and processed data kept out of Git | Large files and third-party texts don't belong in the repo; the pipeline rebuilds them | Committing data, Git LFS |
| 5 | 2026-10-13 | ruff + pre-commit + CI from day one | Consistent style, bugs caught before review, a green badge recruiters can see | Manual checks |
| 6 | 2026-10-13 | Parse PDFs using font size and weight, not plain text | In the Adala PDFs, chapters (16 bold), articles (15 bold), body (14) and footnotes (12) each have their own font. Plain text loses that, and footnotes quote other laws' articles ("Article 34:") that a text-only regex would take for real articles | Regex on plain text, an LLM to split articles |
| 7 | 2026-10-13 | Per-source `LayoutProfile` instead of hard-coded sizes | Each family of PDFs has its own fonts; a new family means a new profile, not a new parser | One parser per document |
| 8 | 2026-10-13 | Drop small superscript digits, keep small superscript letters | Digits are footnote markers ("traitement³"); letters are ordinals that change the meaning ("2e alinéa", "1er") | Drop all small text (lost "2e"), keep all (polluted words) |
| 9 | 2026-10-13 | Never correct the law's wording, even obvious typos | We cite the law: our text must match the source. Typos are recorded in docs/corpus.md instead | Spell-correcting during cleaning |
| 10 | 2026-10-13 | Quality checks that fail the build (numbering gaps, duplicates, short articles, footnote leaks) | A parser that silently loses an article is worse than one that crashes | Manual spot checks only |
