"""Data models for the legal corpus.

`Source` describes one downloaded file (one row of `data/sources.csv`).
`Article` is the unit of everything downstream: we search, cite and verify articles.
"""

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Language = Literal["fr", "ar"]


class Source(BaseModel):
    """Where a legal text comes from, and how to parse it."""

    file: str = Field(description="File name inside data/raw/")
    law_number: str = Field(description='e.g. "09-08"')
    law_title: str
    language: Language
    layout: str = Field(description="Name of the layout profile used to read the PDF")
    source_url: str
    bulletin_officiel: str | None = None
    consolidated_as_of: str | None = None
    downloaded_on: str
    is_official_version: bool = Field(
        description="True only for the Arabic text published in the Bulletin officiel"
    )

    @field_validator("bulletin_officiel", "consolidated_as_of", mode="before")
    @classmethod
    def empty_to_none(cls, value: str | None) -> str | None:
        return value or None


class Article(BaseModel):
    """One article of one law, in one language, with everything needed to cite it."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(description='Stable identifier, e.g. "loi-09-08-fr-art-5"')
    law_number: str
    law_title: str
    language: Language
    article_number: str = Field(description='A string, because some are "25 bis"')
    title: str | None = Field(default=None, description='Optional heading, e.g. "Droit d’accès"')
    hierarchy: list[str] = Field(description="Chapter, then section if any")
    text: str = Field(description="May be empty only if parsing failed; quality checks flag it")
    page_start: int = Field(ge=1)
    source_url: str
    bulletin_officiel: str | None = None
    consolidated_as_of: str | None = None
    is_official_version: bool
    # The word the law itself uses: old dahirs and the codes of 1913–1962 number "الفصل 230",
    # newer laws "المادة 5". None means the usual word for the language.
    article_word: str | None = None

    @property
    def version(self) -> str | None:
        """When this text was last updated, as precisely as known: the consolidation date the
        PDF states ("15 أكتوبر 1954"), else the day Adala published this version of the PDF."""
        if self.consolidated_as_of:
            return self.consolidated_as_of
        found = re.search(r"/uploads/(\d{4})/(\d{2})/(\d{2})/", self.source_url)
        return "-".join(found.groups()) if found else None

    @property
    def label(self) -> str:
        """How to name this article in a citation: "Article", "المادة" or "الفصل"."""
        return self.article_word or ("Article" if self.language == "fr" else "المادة")
