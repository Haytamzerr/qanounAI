# Corpus

The legal texts the assistant can answer from. Each file is listed in [`data/sources.csv`](../data/sources.csv)
with its download URL; the PDFs themselves are not committed.

| Law | Language | Articles | Source | Bulletin officiel | Consolidated as of | Official version? |
| --- | --- | --- | --- | --- | --- | --- |
| 09-08, protection of personal data | French | 67 | [Adala](https://adala.justice.gov.ma/api/uploads/2024/04/30/Protection%20des%20personnes%20physiques-1714464099884.pdf) | n° 5714 of 5 March 2009 | not stated in the PDF | No (French is a translation; the Arabic BO text is official) |

## How to rebuild it

1. Download each PDF from the URL in `data/sources.csv` into `data/raw/`, using the file name given there.
2. Run `uv run python -m qanoun.ingestion.build`.
3. Read `data/interim/<file>.txt` to check the result by eye; the dataset is `data/processed/articles.jsonl`.

## Known issues in the source documents

Kept as they are, because the assistant must quote the law exactly.

| Law | Where | Issue |
| --- | --- | --- |
| 09-08 (fr) | Article 1, definition 7 | "sous- traitant" has a stray space in the PDF |
| 09-08 (fr) | Chapter VI heading | "L’USAGEDE" is missing a space in the PDF |
| 09-08 (fr) | Whole file | No consolidation date; amendments after 2009 may be missing |

## What the PDF layout looks like (Adala, Word export)

| Font | Meaning | What the parser does |
| --- | --- | --- |
| 22 and 21 bold | Cover title, dahir title | Skipped (before the first chapter) |
| 16 bold | Chapter heading, may wrap on several lines | Becomes `hierarchy[0]` |
| 15 bold | "Article premier", "Article 2"… | Starts a new article |
| 14 bold | "Section …" or an article sub-title ("Droit d’accès") | `hierarchy[1]` or `title` |
| 14 | Text of the law | Article text; paragraphs rebuilt from vertical spacing |
| 12 to 13.6 | Footnotes, often quoting other texts | Dropped |
| 9 | Footnote markers (digits) and ordinals (letters) | Markers dropped, ordinals kept |
