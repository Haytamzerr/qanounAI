# Corpus

The legal texts the assistant can answer from. Each file is listed in [`data/sources.csv`](../data/sources.csv)
with its download URL; the PDFs themselves are not committed.

| Law | Language | Articles | Source | Bulletin officiel | Consolidated as of | Official version? |
| --- | --- | --- | --- | --- | --- | --- |
| 09-08, protection of personal data | Arabic | 67 | [Adala](https://adala.justice.gov.ma/api/uploads/2024/09/05/%D8%B8%D9%87%D9%8A%D8%B1%20%D8%B4%D8%B1%D9%8A%D9%81%20%D8%B1%D9%82%D9%85%201.09.15%20%D8%A8%D8%AA%D9%86%D9%81%D9%8A%D8%B0%20%D8%A7%D9%84%D9%82%D8%A7%D9%86%D9%88%D9%86%20%D8%B1%D9%82%D9%85%2009.08%20%D8%A7%D9%84%D9%85%D8%AA%D8%B9%D9%84%D9%82%20%D8%A8%D8%AD%D9%85%D8%A7%D9%8A%D8%A9%20%D8%A7%D9%84%D8%A3%D8%B4%D8%AE%D8%A7%D8%B5%20%D8%A7%D9%84.._-1725534598486.pdf) | n° 5711 of 23 February 2009 (Arabic edition, p. 552) | not stated in the PDF | **Yes** |
| 09-08, protection of personal data | French | 67 | [Adala](https://adala.justice.gov.ma/api/uploads/2024/04/30/Protection%20des%20personnes%20physiques-1714464099884.pdf) | n° 5714 of 5 March 2009 | not stated in the PDF | No (French is a translation; the Arabic BO text is official) |

The French and Arabic versions have the same 67 articles, so `loi-09-08-fr-art-N` and `loi-09-08-ar-art-N` are translations of each other (checked by a test).

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
| 09-08 (ar) | Whole file | No consolidation date |
| 09-08 (ar) | Article 5 and a few lists | Bullets drawn with the Symbol font are dropped with the small text; the list items themselves are kept |

## Arabic PDFs: two extraction traps and how they are repaired

| Trap | What it looks like | Repair (`pdf_lines.py`) |
| --- | --- | --- |
| Ligatures read backwards | "الأولى" read as "األولى", "ألا" as "أال", "لله" as "هلل" (707 cases in Law 09-08) | In a ligature every letter but the last has zero width: a zero-width alef before a lam, or a zero-width run starting with ه, is reversed (`fix_ligatures`) |
| Spaces and punctuation out of place | ".الخاصة" instead of "الخاصة.", "المادةالأولى" with no space | Characters are re-ordered from their positions on the page, right to left, keeping numbers like "09.08" left to right (`reading_order`) |

A blind "swap the letters back" rule would be wrong: "ال" is also the ordinary definite article, and "الإلكتروني" legitimately contains "لإل". The width test only touches real ligatures.

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

Arabic files (`adala-word-ar` profile): chapters (الباب) 20 bold, sections (الفرع) 19 bold, article sub-titles 18 bold, articles (المادة الأولى، المادة 2…) 16 bold, text 16, footnotes 13, markers 10.6.
