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
| 11 | 2026-10-13 | Repair Arabic ligatures using glyph width, not text patterns | Ligature letters come out reversed; the zero width of all but the last letter identifies them exactly. Text patterns can't tell a broken "أل" from a real one ("الإلكتروني") | Find-and-replace on letter pairs, OCR |
| 12 | 2026-10-13 | Rebuild Arabic reading order from character positions | The extractor misplaces spaces, punctuation and quotes in right-to-left text, but their positions are reliable | Full Unicode bidi algorithm on the extracted text, other PDF libraries |
| 13 | 2026-10-13 | One parser for both languages: fonts in `LayoutProfile`, heading words in `LanguageRules` | French and Arabic laws share the same structure; only fonts and words differ | Separate French and Arabic parsers |
| 14 | 2026-10-13 | Same article ids across languages (`loi-09-08-fr-art-N` / `-ar-art-N`) | Lets the assistant show the official Arabic text next to the French one, and match a question in one language to the article in the other | A separate translation table |
| 15 | 2026-10-13 | Rebuild each line from all its characters, ignoring how the PDF cuts it into spans | The Labour Code splits words and shadowed headings into pieces that, ordered piece by piece, interleave. Ordering the whole line by position is independent of the cut | Fixing span boundaries case by case |
| 16 | 2026-10-13 | Drop shadow copies by comparing character, font, width and position (≤ 1.5 pt) | Headings are drawn twice for a shadow effect. Comparing widths keeps the hidden zero-width alef of a ligature, which a position-only rule deleted ("الاتفاقيات" → "التفاقيات") | Removing duplicate lines, image-based OCR |
| 17 | 2026-10-13 | Rescue article headings printed in the footnote font, and report each rescue | "المادة 517" is mis-formatted in the official PDF; without the rescue, article 517 silently merges into 516. The quality check caught it through the numbering gap | Hard-coding a fix for article 517 |
| 18 | 2026-10-13 | Heading levels as an ordered list per layout (book → sub-section) | Codes have up to 5 levels, small laws 2; one parser handles any depth | A fixed chapter/section model |
| 19 | 2026-10-13 | Use the consolidated Arabic Labour Code (16 July 2026) as the main source | It is official and current; the French version on Adala dates from 2011 and misses 15 years of amendments | Using the outdated French text |
| 20 | 2026-10-13 | Any change to the PDF reader is checked by rebuilding earlier laws and comparing them word for word | A repair for one document must not silently change another | Relying on tests only |
| 21 | 2026-10-13 | A heading's level is decided by its font **and** its first word together | In the Family Code, chapters and sections share one font; size alone put sections at the wrong level | Size only, position on the page |
| 22 | 2026-10-13 | A short article is suspicious only if it is tiny (< 15 chars) or doesn't end like a sentence | 14 real one-line articles were flagged ("سن الرشد القانوني 18 سنة شمسية كاملة."); truncated articles end without final punctuation | A fixed length threshold |
