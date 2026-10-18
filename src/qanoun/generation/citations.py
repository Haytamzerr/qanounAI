"""Check every citation before an answer is shown.

A legal assistant that invents an article is worse than one that says "I don't know". So the
model's answer is checked, not trusted:

1. every source marker [n] must be one of the sources we gave; unknown ones are removed;
2. an answer that states rules must cite at least one source;
3. every article number written in the text ("المادة 13", "article 13", "lmadda 13") must be a
   cited source, or be mentioned inside one ("…under article 37…"); otherwise the model is
   citing from memory.

The result lists the problems found; the caller decides whether to retry or to warn the user.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass, field

from qanoun.ingestion.models import Article

MARKER = re.compile(r"\[(\d+)\]")
ARTICLE_MENTION = re.compile(
    r"(?:المادة|المواد|الفصل|\barticles?\b|\bart\.|\bl?mad+[ae]\b)\s*(\d+)", re.IGNORECASE
)


@dataclass
class CheckedAnswer:
    text: str  # with unknown markers removed
    cited: list[int]  # source numbers, 1-based, in order of first use
    problems: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problems


def check(
    text: str,
    sources: Sequence[Article],
    used: Sequence[int] = (),
    answered: bool = True,
    allowed: set[str] | frozenset[str] = frozenset(),
) -> CheckedAnswer:
    """`allowed`: article numbers the question itself mentions, which the answer may repeat
    (to say "article 1500 does not exist")."""
    problems = []
    valid = range(1, len(sources) + 1)

    def keep_known(match: re.Match) -> str:
        if int(match.group(1)) in valid:
            return match.group(0)
        problems.append(f"marker [{match.group(1)}] is not one of the {len(sources)} sources")
        return ""

    cleaned = MARKER.sub(keep_known, text)
    cited = list(dict.fromkeys(int(n) for n in MARKER.findall(cleaned)))
    cited += [n for n in dict.fromkeys(used) if n in valid and n not in cited]

    if answered and not cited:
        problems.append("the answer cites no source")

    allowed = set(allowed) | {sources[n - 1].article_number.split()[0] for n in cited}
    for n in cited:
        allowed.update(ARTICLE_MENTION.findall(sources[n - 1].text))
    for number in dict.fromkeys(ARTICLE_MENTION.findall(cleaned)):
        if number not in allowed:
            problems.append(f"mentions article {number}, which is not among the cited sources")

    return CheckedAnswer(re.sub(r"[ \t]{2,}", " ", cleaned).strip(), cited, problems)
