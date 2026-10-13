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
