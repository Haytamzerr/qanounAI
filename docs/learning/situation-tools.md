# How the situation tools work — explained simply

*Decisions 81–86. Format: ✍️ notes · 🏠 real-life example · 🎤 interview sentence · 📝 summary.*

The "Analyse my situation" page turns a vague problem into a file, and the analysis into
action: **what the law says → before when → how much → with which letter.** Eleven techniques
make that work. Each one answers a question a real person asks.

---

## 1. A guided form that writes a case file (decision 81)

✍️ **Notes**
- One big text box intimidates people; they forget the facts that matter (their role, the date,
  their proof). Six short steps ask for them one at a time: *theme → role → what happened +
  proof → when → what you want → review.* This is called **progressive disclosure**: show only
  what is needed now.
- The "case file" beside the steps is rebuilt from a single JavaScript object (`file`) after
  every tap: one source of truth, many views.
- The page is a **hash route** (`#situation`): same HTML file, the script shows one section
  and hides the other. The browser's back button works, nothing to build or install.
- The choices travel to the API as `facts` (at most 6, 200 characters each), *separate* from
  the person's own words. The language of the answer is detected on their words only, so
  French labels never turn a Darija story into a French answer.

🏠 **Real-life example** — a good doctor's receptionist doesn't hand you a blank page; she asks
"what's it about? since when? do you have your test results?" and fills the form as you talk.

🎤 *"I replaced the free-text box with a six-step guided intake that builds a structured case
file live; the structured facts are sent separately from the free text so language detection
and search stay driven by the user's own words."*

📝 Guided steps · one state object, several views · hash routing · facts kept separate from text.

---

## 2. Ready-made situations (decision 85)

✍️ Nine common cases (dismissed without reason, unpaid salary, landlord won't repair, eviction
without a judgment, unpaid debt, bounced cheque, defective product, road accident, custody and
alimony) pre-fill the whole file in the interface language. The person lands on the story step
and **edits** instead of writing from nothing. These are templates, not answers: the analysis
still runs on the official texts.

🏠 A form letter at the post office: you change the names and dates instead of writing it all.

🎤 *"Templates lower the blank-page cost: one tap fills a realistic case the user then edits."*

📝 Templates → faster start, same verified analysis.

---

## 3. Reading the person's document (decision 86)

✍️ **Two paths, chosen by the file:**
| File | How it is read | Can quotes be checked? |
|---|---|---|
| PDF with text (most contracts) | **PyMuPDF** extracts the text here; only text is sent to Gemini | ✅ every quoted clause must be found in that text, or it is dropped |
| Photo, scanned PDF | sent to Gemini as an image (**multimodal** model) | ❌ marked "read from an image: compare with your document" |

- The model returns a **JSON schema** (kind, summary, story, theme, dates, amounts, clauses).
- **Extractive verification:** asking for the clause's *exact words* lets code check them —
  the same idea as the deadlines (§4). Invented clauses disappear.
- **Privacy by design:** the story is written with roles ("the landlord"), and phone, CIN and
  e-mail patterns are masked (•••) by code before anything goes into the file; the page warns
  that the document is sent to Google Gemini.
- The client (`GeminiLLM.generate`) gained `attachments=[(mime, bytes)]`: Gemini's REST API
  takes files as base64 `inline_data` next to the text.

🏠 A friend reads your contract and highlights three clauses — and you can check each yellow
highlight is really in the contract, not something he imagined.

🎤 *"Text PDFs are parsed locally so every extracted clause is verified as a verbatim substring;
images go through Gemini's vision input and are flagged as unverifiable. PII is masked
deterministically before it reaches the case file."*

📝 Local text extraction when possible · vision when not · quotes verified · PII masked.

---

## 4. Legal deadlines, verified, with a calendar reminder (decision 82)

✍️ **Why:** missing a deadline loses the right ("90 days to take a dismissal to court", Labour
Code art. 65).

**How, in one extra field, no extra Gemini call:** the analysis JSON gains `deadlines`, each
with `what`, `amount`, `unit`, `from_event`, `source` and `quote`. Then **code checks**:
1. the source number exists;
2. the **quote is in the article**, word for word, after the same normalisation as search
   (vowel marks, alif forms, «ى/ي», «ة/ه»);
3. the **duration is in the quote**: digits ("90"), number words ("تسعين", "quinze"), the unit
   alone meaning one ("أجل شهر"), or an Arabic dual meaning two ("شهرين");
4. the unit is days, months, years or hours.

Anything that fails is **dropped**: the test shows an invented "60 days" and "15 days"
disappearing while the real "1 month" stays.

**In the page:** the deadline starts **today by default** — "if I act now, what is my last
day?" — because it usually runs from an event still to come (sending the notice). The person
can change the date; the page computes the last day and the days left (in gold when ≤ 7 days),
and builds an **.ics** file (the iCalendar standard, RFC 5545) with two reminders (3 days
before, the evening before). Phones and Outlook open it directly.

🏠 A friend says "you have a month". You ask "show me where it says that" — and you only write
it in your diary if the page really says so.

🎤 *"Deadlines are extracted in the same structured call as the analysis, then verified
deterministically: the quoted span must occur in the cited article and must contain the stated
duration. Only verified deadlines reach the UI, which turns them into dates and an iCalendar
file with alarms."*

📝 Same call · exact quote · code checks quote + number · dropped if wrong · .ics with alarms.

---

## 5. Calculators: arithmetic in code, rates from the articles (decision 83)

✍️ A language model is weak at arithmetic and may "remember" an old rate. So the **numbers come
from the articles** and the **arithmetic is Python**:

| Calculator | Rule (article) |
|---|---|
| Dismissal indemnity | hourly wage = monthly × 12 ÷ 2,288 h (art. 184); per year: 96 h (years 1–5), 144 h (6–10), 192 h (11–15), 240 h (beyond) (art. 53); only after 6 months (art. 52); +100 % for staff representatives (art. 58) |
| Abusive dismissal damages | 1.5 month per year, max 36 months (art. 41) — the court decides |
| Annual leave | 1.5 day per month (2 under 18) (art. 231) + 1.5 per 5 full years, max 30 (art. 232) |
| Rent increase | max 8 % housing, 10 % professional (Law 67.12 art. 34), only every 3 years (arts. 32–33) |

- Each constant is written **next to its article** (provenance).
- The result is a list of **steps** (`key` + numbers), not sentences: the interface writes them
  in Arabic, French or Darija. Same data, three languages, no translation by the model.
- **Notes** state the honest limits ("a court may count a part-year differently", "the 52-week
  average is the base").
- Worked examples in the tests are checked by hand: 7 years at 5,000 MAD → 768 h × 26.22 =
  **20,139.86 MAD**.
- These pure functions are exactly what an **agent tool** or **MCP server** will expose later.

🏠 You ask a lawyer "how much?". He doesn't guess: he opens the Code, reads the rate, and does
the sum on a calculator in front of you.

🎤 *"I never let the LLM do legal arithmetic: rates are constants with article provenance,
calculations are pure tested functions returning explainable steps, localised by the UI."*

📝 Rates from articles · Python does the maths · steps shown · tests with hand-checked examples.

---

## 6. Letters, drafted from the sources, with blanks instead of guesses (decision 84)

✍️ Three kinds: **notice** (mise en demeure / إنذار) to the other party, **complaint**
(prosecutor, labour inspector…), **request** (court, office). In formal Arabic or French.

- The model may only rely on the articles the answer cited, **named in full**
  ("المادة 10 من القانون رقم 67.12").
- The **same citation checker** as the answers verifies every article number, with one retry.
- **Never invent a fact:** unknown names, addresses, dates are **placeholders** — `[الاسم الكامل]`,
  highlighted in the page so the person sees what to fill in.
- **Word file** with python-docx. Arabic needs Word's own right-to-left markers (`<w:bidi/>` on
  the paragraph, `<w:rtl/>` on the text) or the punctuation ends up on the wrong side.
- **Print** shows only the letter (a print stylesheet hides everything else).

🏠 A public writer (كاتب عمومي) outside the court: he writes the formal letter from your story
and the law, and leaves blanks for the details only you know.

🎤 *"Letter drafting reuses the citation verifier and replaces unknown facts with explicit
placeholders, so the model can't fabricate names or dates; output is a bidi-correct DOCX."*

📝 Sources only · checked citations · placeholders · Word (RTL) · print.

---

## 7. A bug the letters revealed: «للمادة» escaped the checker

✍️ The checker found article numbers after «المادة». But Arabic glues «ل» to the word and the
alif disappears: «طبقا **للمادة** 999» does not contain «المادة». A letter test citing a fake
article 999 passed. Fixed pattern: `(ال|لل)(مادة|مواد|فصل|فصول)`, plus a **regression test**.
This protected the normal answers too.

🎤 *"Writing tests for a new feature exposed a gap in an old safety check — Arabic prefix
morphology — which I fixed with a regression test."*

📝 New tests can find old bugs; Arabic morphology matters in regexes.

---

## 8. Listening and dictating: the browser's own speech (Web Speech API)

✍️ `speechSynthesis` reads the answer aloud (Arabic or French voice of the device);
`SpeechRecognition` dictates the story. Both are **feature-detected**: if the browser lacks
them, the button is hidden. Hidden too for Arabizi answers (no voice reads Latin-letter Darija
well). Free, offline-capable, nothing sent to us.

🏠 Like a phone's "read aloud" button — it uses what the phone already has.

📝 Built into browsers · feature detection · hidden when it would sound wrong.

---

## 9. Turning the analysis into actions

✍️ Small changes, big effect:
- "What you can do" becomes a **checklist** you can tick.
- Each "missing fact" question is a **button** that fills the follow-up box.
- **Print / PDF** of the answer, **edit the file** from the answer.

📝 From reading to doing.

---

## 10. How it was tested

✍️
- **Scripted model** (`ScriptedLLM`): replies are written in advance, so every path (good
  deadline, invented deadline, wrong article in a letter, photo vs text PDF) is tested without
  Gemini and without cost.
- **Hand-checked examples** for every calculator.
- **Browser test** (Playwright): upload a document → steps → analysis → calculator → calendar
  file (checked: valid iCalendar) → letter → Word file (checked: valid ZIP) → screenshots in
  Arabic, Darija, French, desktop and phone.

🎤 *"Every LLM-dependent path is tested with a scripted fake model, the numeric tools with
hand-verified examples, and the whole flow end-to-end in a headless browser."*

📝 Fake model · worked examples · end-to-end browser test.

---

## The one-minute version (for an interview)

> "The situation page guides people through six steps and builds a structured case file — or
> fills it from their contract. The analysis then adds three things a lawyer would: **deadlines**,
> extracted in the same model call but verified against the exact words of the article before
> being turned into calendar reminders; **calculators** where the rates come from the articles
> and the arithmetic is tested Python, never the model; and **letters** drafted only from the
> cited articles, checked by the same citation verifier, with placeholders instead of invented
> facts. The theme across all of it: the model proposes, deterministic code verifies."
