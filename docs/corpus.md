# Corpus

The five hand-checked texts below are the **core corpus** used by the evaluations. The assistant
also answers from every law on Adala: see [the full corpus](#the-full-corpus-every-law-on-adala).

The core texts: Each file is listed in [`data/sources.csv`](../data/sources.csv)
with its download URL; the PDFs themselves are not committed.

| Law | Language | Articles | Source | Bulletin officiel | Consolidated as of | Official version? |
| --- | --- | --- | --- | --- | --- | --- |
| 09-08, protection of personal data | Arabic | 67 | [Adala](https://adala.justice.gov.ma/api/uploads/2024/09/05/%D8%B8%D9%87%D9%8A%D8%B1%20%D8%B4%D8%B1%D9%8A%D9%81%20%D8%B1%D9%82%D9%85%201.09.15%20%D8%A8%D8%AA%D9%86%D9%81%D9%8A%D8%B0%20%D8%A7%D9%84%D9%82%D8%A7%D9%86%D9%88%D9%86%20%D8%B1%D9%82%D9%85%2009.08%20%D8%A7%D9%84%D9%85%D8%AA%D8%B9%D9%84%D9%82%20%D8%A8%D8%AD%D9%85%D8%A7%D9%8A%D8%A9%20%D8%A7%D9%84%D8%A3%D8%B4%D8%AE%D8%A7%D8%B5%20%D8%A7%D9%84.._-1725534598486.pdf) | n° 5711 of 23 February 2009 (Arabic edition, p. 552) | not stated in the PDF | **Yes** |
| 09-08, protection of personal data | French | 67 | [Adala](https://adala.justice.gov.ma/api/uploads/2024/04/30/Protection%20des%20personnes%20physiques-1714464099884.pdf) | n° 5714 of 5 March 2009 | not stated in the PDF | No (French is a translation; the Arabic BO text is official) |

| 65-99, Labour Code (مدونة الشغل) | Arabic | 589 | [Adala](https://adala.justice.gov.ma/api/uploads/2026/07/28/%D8%B8%D9%87%D9%8A%D8%B1%20%D8%B4%D8%B1%D9%8A%D9%81%20%D8%B1%D9%82%D9%85%201.03.194%20%D8%A8%D8%AA%D9%86%D9%81%D9%8A%D8%B0%20%D8%A7%D9%84%D9%82%D8%A7%D9%86%D9%88%D9%86%20%D8%B1%D9%82%D9%85%2065.99%20%D8%A7%D9%84%D9%85%D8%AA%D8%B9%D9%84%D9%82%20%D8%A8%D9%85%D8%AF%D9%88%D9%86%D8%A9%20%D8%A7%D9%84%D8%B4%D8%BA%D9%84%20-1785240385771.pdf) | n° 5167 of 8 December 2003; last amendment BO n° 7526 of 16 July 2026 (Law 032.26) | **16 July 2026** | **Yes** |

| 70-03, Family Code (مدونة الأسرة) | Arabic | 400 | [Adala](https://adala.justice.gov.ma/api/uploads/2024/07/22/%D9%85%D8%AF%D9%88%D9%86%D8%A9%20%D8%A7%D9%84%D8%A3%D8%B3%D8%B1%D8%A9-1721646687560.pdf) | n° 5184 of 5 February 2004; last amendment Law 65.21, BO n° 7008 of 29 July 2021 | 29 July 2021 | **Yes** |
| 31-08, Consumer Protection (حماية المستهلك) | Arabic | 206 | [Adala](https://adala.justice.gov.ma/api/uploads/2024/10/29/%D8%B8%D9%87%D9%8A%D8%B1%20%D8%B4%D8%B1%D9%8A%D9%81%20%D8%B1%D9%82%D9%85%20%20%D8%A8%D8%AA%D8%AD%D8%AF%D9%8A%D8%AF%20%D8%AA%D8%AF%D8%A7%D8%A8%D9%8A%D8%B1%20%D9%84%D8%AD%D9%85%D8%A7%D9%8A%D8%A9%20%D8%A7%D9%84%D9%85%D8%B3%D8%AA%D9%87%D9%84%D9%83-1730189983480.pdf) | n° 5932 of 7 April 2011; last amendment Law 78.20, BO n° 6945 of 21 December 2020 | 21 December 2020 | **Yes** |

**Total: 1,329 articles in 5 texts.**

The Family Code is under reform discussions; check before any demo whether a newer consolidated version has been published. The Labour Code has no up-to-date French text (Adala's French version dates from October 2011), so French questions are answered from the official Arabic text.

For Law 09-08, the French and Arabic versions have the same 67 articles, so `loi-09-08-fr-art-N` and `loi-09-08-ar-art-N` are translations of each other (checked by a test).

## The full corpus: every law on Adala

Beyond the five texts above, the assistant can answer from every law published on
[Adala](https://adala.justice.gov.ma), the Ministry of Justice's portal (`QANOUN_CORPUS=full`, decision 64).

| Step | Command | Result (14 October 2026) |
| --- | --- | --- |
| Catalogue | `uv run python -m qanoun.ingestion.adala catalog` | 5,507 documents, 63 subjects, all in Arabic |
| Download the laws | `uv run python -m qanoun.ingestion.adala download` | 971 PDFs, 1.3 GB, 17,755 pages |
| Parse | `uv run python -m qanoun.ingestion.adala_parse` | 798 laws → 778 parsed, **32,777 articles** in `data/processed/adala_articles.jsonl`, one line per law in `adala_report.csv` |

Left out on purpose (decisions 62 and 65): annual finance laws, laws marked repealed, the 1962–1992
constitutions, international treaties, older PDFs of the same law, repealed articles. Not parsed: 16 texts without article
headings (appointments, one-decision dahirs) and 4 scanned PDFs (they would need OCR).

The parser measures each PDF's fonts instead of using a hand-made profile (decision 60). Its report
flags 164 laws with a gap in the article numbers: almost always repealed articles that were removed,
or articles the consolidated text itself skips (Penal Code 19 to 23).

Largest texts: Obligations and Contracts (الفصل, 1,313 articles), Criminal Procedure (914), Commerce
(823), Penal Code (723), Civil Procedure 58.25 (644), Highway Code (328), Real Rights (333).

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
| 65-99 (ar) | Article 517 | The heading "المادة 517" is printed in the footnote font (12.8 pt). It is rescued automatically (see below) and reported by the build |
| 65-99 (ar) | Chapter headings | Drawn twice with a 0.8 pt offset (shadow effect); the copy is removed |
| 09-08 (ar) | Article 5 and a few lists | Bullets drawn with the Symbol font are dropped with the small text; the list items themselves are kept |

## Arabic PDFs: two extraction traps and how they are repaired

| Trap | What it looks like | Repair (`pdf_lines.py`) |
| --- | --- | --- |
| Ligatures read backwards | "الأولى" read as "األولى", "ألا" as "أال", "لله" as "هلل" (707 cases in Law 09-08) | In a ligature every letter but the last has zero width: a zero-width alef before a lam, or a zero-width run starting with ه, is reversed (`fix_ligatures`) |
| Spaces and punctuation out of place | ".الخاصة" instead of "الخاصة.", "المادةالأولى" with no space | Characters are re-ordered from their positions on the page, right to left, keeping numbers like "09.08" left to right (`reading_order`) |

| Shadowed headings | "البابالباب الأول: لأول: فترة الاترة الا ختبار": the heading is drawn twice, 0.8 pt apart | A glyph identical in character, font and width, within 1.5 pt of one already kept in another span, is dropped (`_ShadowFilter`) |
| Fake spaces | "الم اد ة": "spaces" whose box starts inside a letter | Spaces that start inside a letter are removed (`drop_fake_spaces`) |
| Pieces cut anywhere | Words and headings split across spans, the two shadow copies split differently | Each visual line is rebuilt from all of its characters at once, whatever the spans (`group_into_lines`) |

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

Arabic Labour Code (`adala-code-ar` profile): books (الكتاب) 21.8 bold, titles (القسم) 21.0 bold, chapters (الباب) 20.3 bold, sections (الفرع) 18.8 bold, sub-sections (القسم الفرعي) 18.0 bold, articles 15.8 bold, text 15.8, footnotes 12.8.

Family Code (`adala-family-ar`): books 22 bold, titles 20 bold, chapters **and** sections both 18 bold (told apart by their first word), articles 16 bold, text 16, paragraphs 34 pt apart. The first articles sit under "باب تمهيدي" (preliminary chapter, without "ال").
Consumer Protection (`adala-consumer-ar`): titles 22.1 bold, chapters 21.1 bold, sections 19.9 bold ("الفرع 1"), articles 16.1 bold, text 16.1; page numbers are bold.

## Mis-formatted article headings

A small line that is exactly an article heading (no colon) and is directly followed by body text is promoted back to an article heading (`rescue_misformatted_headings`). Footnotes quoting other texts end with a colon, or are followed by small text or the page number, so they are never promoted. Every rescue is printed by the build as a `note:` line.

Arabic files (`adala-word-ar` profile): chapters (الباب) 20 bold, sections (الفرع) 19 bold, article sub-titles 18 bold, articles (المادة الأولى، المادة 2…) 16 bold, text 16, footnotes 13, markers 10.6.
