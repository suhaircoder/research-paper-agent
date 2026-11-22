"""Split a paper into the sections a reader looks up."""

from __future__ import annotations

import re

BUCKETS = {
    "abstract": "abstract",
    "introduction": "introduction",
    "literature review": "related",
    "related work": "related",
    "material and methods": "method",
    "materials and methods": "method",
    "proposed methodology": "method",
    "proposed method": "method",
    "methodology": "method",
    "method": "method",
    "methods": "method",
    "approach": "method",
    "experiments": "experiments",
    "experimental results": "experiments",
    "results and discussion": "experiments",
    "results": "experiments",
    "conclusion": "conclusion",
    "conclusions": "conclusion",
    "limitations": "conclusion",
}

HEADER_RE = re.compile(
    r"^(?:(?P<num>\d+(?:\.\d+)*)\.?\s+)?"
    r"(?P<label>abstract|introduction|literature review|related work|materials and methods|material and methods|"
    r"proposed methodology|proposed method|methodology|methods|method|approach|"
    r"experimental results|experiments|results and discussion|results|conclusions|conclusion|limitations)"
    r"\b[:\s-]*(?P<rest>.*)$",
    re.IGNORECASE,
)

END_RE = re.compile(
    r"^(author contributions|funding|institutional review board statement|informed consent statement|"
    r"data availability statement|acknowledgments|acknowledgements|conflicts of interest|"
    r"references|reference|abbreviations|publisher'?s note)\b",
    re.IGNORECASE,
)

PAGE_RE = re.compile(r"\b\d+\s+of\s+\d+\s*$", re.IGNORECASE)
ARTICLE_LABELS = {"article", "review", "communication", "brief report"}
FRONT_MATTER_RE = re.compile(
    r"^(academic editor|received|revised|accepted|published|citation|copyright|licensee|"
    r"this article|distributed under|keywords)\b",
    re.IGNORECASE,
)


def split_sections(text: str) -> dict[str, str]:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"-\n(?=[a-z])", "", text)
    lines = text.split("\n")
    marks = _marks(lines)
    sections = {name: "" for name in ("title", "abstract", "introduction", "related", "method", "experiments", "conclusion")}
    if not marks:
        body = " ".join(text.split())
        sections["abstract"] = body
        sections["title"] = _title_from(body)
        return sections
    preamble = [line.strip() for line in lines[: marks[0][0]] if line.strip()]
    sections["title"] = _title_from_lines(preamble)
    for index, (start, name, prefix) in enumerate(marks):
        if name is None:
            continue
        end = marks[index + 1][0] if index + 1 < len(marks) else len(lines)
        body = " ".join(_kept_line(line) for line in lines[start + 1 : end] if _kept_line(line))
        if prefix:
            body = f"{prefix} {body}".strip()
        sections[name] = f"{sections[name]} {body}".strip()
    sections["abstract"] = re.split(r"\bKeywords\s*:", sections["abstract"], maxsplit=1, flags=re.IGNORECASE)[0].strip()
    if not sections["title"]:
        sections["title"] = _title_from(sections["abstract"])
    return sections


def _marks(lines: list[str]) -> list[tuple[int, str | None, str]]:
    marks: list[tuple[int, str | None, str]] = []
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if END_RE.match(stripped):
            marks.append((index, None, ""))
            continue
        match = HEADER_RE.match(stripped)
        if not match or not _is_heading(stripped, match):
            continue
        label = match.group("label").lower()
        rest = (match.group("rest") or "").strip()
        prefix = rest if label == "abstract" else ""
        marks.append((index, BUCKETS[label], prefix))
    return marks


def _is_heading(line: str, match: re.Match[str]) -> bool:
    label = match.group("label").lower()
    rest = (match.group("rest") or "").strip()
    if label == "abstract":
        return True
    if "." in rest:
        return False
    if match.group("num"):
        return len(line) <= 180
    return rest == ""


def _kept_line(line: str) -> str:
    stripped = line.strip()
    if not stripped or (PAGE_RE.search(stripped) and len(stripped) < 80):
        return ""
    return stripped


def _title_from_lines(lines: list[str]) -> str:
    for index, line in enumerate(lines):
        if line.lower() in ARTICLE_LABELS:
            title_lines = []
            for follow in lines[index + 1 :]:
                if re.search(r"\d", follow):
                    break
                title_lines.append(follow)
            if title_lines:
                return " ".join(title_lines)[:180]
    kept = [line for line in lines if not FRONT_MATTER_RE.match(line) and "http" not in line.lower() and "doi.org" not in line.lower()]
    return _title_from(" ".join(kept))


def _title_from(text: str) -> str:
    line = text.strip().split(".")[0].strip()
    return line[:180] if line else "Untitled paper"
