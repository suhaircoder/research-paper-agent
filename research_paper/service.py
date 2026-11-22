"""Turn an uploaded paper, or the practice papers, into a brief."""

from __future__ import annotations

from pathlib import Path

from research_paper.compare import Comparison, compare_briefs
from research_paper.extract import PaperBrief, extract_brief
from research_paper.llm import refine_brief
from research_paper.read import load_text
from research_paper.samples import MORPH_NET, SYNC_FACE
from research_paper.sections import split_sections


def brief_from_text(text: str, *, use_model: bool = False) -> PaperBrief:
    sections = split_sections(text)
    brief = extract_brief(sections)
    if use_model:
        return refine_brief(sections, brief)
    return brief


def brief_from_file(path: str, *, use_model: bool = False) -> PaperBrief:
    brief = brief_from_text(load_text(path), use_model=use_model)
    if brief.title == "Untitled paper":
        brief.title = Path(path).stem
    return brief


def practice_pair(*, use_model: bool = False) -> tuple[PaperBrief, PaperBrief, Comparison]:
    left = brief_from_text(SYNC_FACE, use_model=use_model)
    right = brief_from_text(MORPH_NET, use_model=use_model)
    return left, right, compare_briefs(left, right)


def analyze_upload(first: str, second: str = "", *, use_model: bool = False) -> tuple[PaperBrief, PaperBrief | None, Comparison | None]:
    left = brief_from_file(first, use_model=use_model)
    if not second:
        return left, None, None
    right = brief_from_file(second, use_model=use_model)
    return left, right, compare_briefs(left, right)
