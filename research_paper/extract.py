"""Pull the method, datasets, and reported numbers out of paper sections."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

DATASETS = (
    "VoxCeleb2",
    "VoxCeleb",
    "CelebA-HQ",
    "CelebA",
    "FFHQ",
    "HDTF",
    "LRS3",
    "LRS2",
    "MEAD",
    "CREMA-D",
    "AFLW2000",
    "Florence",
    "ImageNet",
    "COCO",
    "BIWI",
    "300W",
    "NoW",
    "VisDrone2019",
    "VisDrone",
    "UAVDT",
    "DOTA",
    "SMOT4SB",
)

METRIC_NAMES = r"FID|PSNR|SSIM|LPIPS|LSE-D|LSE-C|NME|AKD|mAP(?:@?\d+(?:\.\d+)?)?|IoU|F1|HOTA|accuracy"
METRIC_RE = re.compile(
    rf"\b({METRIC_NAMES})\b(?:[^.]{{0,48}}?)(\d+(?:\.\d+)?)\s*(%|dB)?",
    re.IGNORECASE,
)
METRIC_BEFORE_RE = re.compile(
    rf"(\d+(?:\.\d+)?)\s*(%|dB)?\s*\b({METRIC_NAMES})\b",
    re.IGNORECASE,
)

SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
LIMIT_RE = re.compile(r"\b(however|limitation|limitations|struggles|struggle|cannot|fails|fail)\b", re.IGNORECASE)
PROPOSE_RE = re.compile(
    r"\b(we propose|we proposed|we present|we introduce|our method|our proposed|the main objective of this study|this study focuses on|this study investigates)\b",
    re.IGNORECASE,
)
DATASET_PHRASE_RE = re.compile(
    r"\b([A-Z][A-Za-z0-9-]*(?:\s+(?:of|the|and|for|[A-Z][A-Za-z0-9-]*)){0,6})\s+[Dd]atasets?\b"
)
DATASET_CODE_RE = re.compile(r"\(([A-Z][A-Z0-9-]{2,})\)\s+[Dd]atasets?\b")
SKIP_DATASET_WORDS = {
    "data",
    "training",
    "testing",
    "test",
    "original",
    "sample",
    "samples",
    "dataset",
    "our",
    "the",
    "this",
    "split",
    "after",
    "increase",
    "using",
    "weight",
    "weights",
    "expansion",
    "bootstrap",
    "divide",
    "another",
    "balanced",
    "imbalanced",
    "above",
    "given",
    "following",
}


@dataclass
class PaperBrief:
    title: str
    problem: str
    method: str
    datasets: list[str] = field(default_factory=list)
    metrics: list[tuple[str, str]] = field(default_factory=list)
    limitation: str = ""
    reader: str = "paper text"

    @property
    def metric_names(self) -> set[str]:
        return {name for name, _value in self.metrics}


def sentences(text: str) -> list[str]:
    parts = SENTENCE_RE.split(text.strip())
    return [part.strip() for part in parts if part.strip()]


def extract_brief(sections: dict[str, str]) -> PaperBrief:
    abstract = sections.get("abstract", "")
    method_text = sections.get("method", "")
    experiments = sections.get("experiments", "")
    conclusion = sections.get("conclusion", "")
    introduction = sections.get("introduction", "")
    own_text = " ".join(part for part in (abstract, method_text, experiments) if part)
    datasets = _datasets(own_text) or _datasets(introduction) or _datasets(sections.get("related", ""))
    return PaperBrief(
        title=sections.get("title") or "Untitled paper",
        problem=_problem(abstract, introduction),
        method=_method(method_text, abstract, introduction),
        datasets=datasets,
        metrics=_metrics(experiments or method_text or abstract),
        limitation=_limitation(conclusion, introduction),
    )


def _problem(abstract: str, introduction: str = "") -> str:
    found = _readable_sentences(abstract) or _readable_sentences(introduction)
    if not found:
        return "The paper does not state the problem in an abstract."
    return " ".join(found[:2])[:500]


def _method(method_text: str, abstract: str, introduction: str = "") -> str:
    found = _readable_sentences(method_text)
    for index, sentence in enumerate(found):
        if PROPOSE_RE.search(sentence):
            return " ".join(found[index : index + 2])[:500]
    if found:
        return " ".join(found[:2])[:500]
    for sentence in _readable_sentences(abstract) + _readable_sentences(introduction):
        if PROPOSE_RE.search(sentence):
            return sentence[:500]
    return "The method section was not found."


def _readable_sentences(text: str) -> list[str]:
    found = []
    for sentence in sentences(text):
        sentence = _strip_glued_heading(sentence)
        if _readable(sentence):
            found.append(sentence)
    return found


def _strip_glued_heading(sentence: str) -> str:
    cleaned = re.split(r"\s+\d+(?:\.\d+)+\s+(?=[A-Z])", sentence, maxsplit=1)[0]
    cleaned = re.sub(r"\[\d+(?:[-,]\d+)*\]", "", cleaned).strip()
    lead = re.match(
        r"^(?:\d+(?:\.\d+)+\s+)?(?:[A-Z][A-Za-z]+(?:\s+(?:of|the|and|for|[A-Z][A-Za-z]+)){0,8})\s+(?=[A-Z][a-z])",
        cleaned,
    )
    if lead and len(cleaned) - lead.end() > 40:
        cleaned = cleaned[lead.end() :]
    match = re.match(r"^(?:[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,4})\s+(?=[A-Z][a-z])", cleaned)
    if match and len(cleaned) - match.end() > 40:
        cleaned = cleaned[match.end() :]
    return cleaned.strip()


def _readable(sentence: str) -> bool:
    cleaned = sentence.strip().strip(".")
    if re.fullmatch(r"\d+(?:\.\d+)*", cleaned):
        return False
    return len(re.findall(r"[A-Za-z]{3,}", cleaned)) >= 5


def _datasets(text: str) -> list[str]:
    found: list[tuple[int, str]] = []
    for name in DATASETS:
        match = re.search(rf"\b{re.escape(name)}\b", text)
        if match:
            found.append((match.start(), name))
    phrases: list[tuple[int, str]] = []
    used: list[tuple[int, str]] = []
    for match in DATASET_CODE_RE.finditer(text):
        phrases.append((match.start(), match.group(1)))
    for match in DATASET_PHRASE_RE.finditer(text):
        phrase = re.sub(r"\s+", " ", match.group(1)).strip()
        if not _named_dataset(phrase):
            continue
        name = f"{phrase} Dataset"
        if any(re.search(rf"\b{re.escape(known)}\b", name) for known in DATASETS):
            continue
        if re.match(r"\s+and\b", text[match.end() : match.end() + 8], re.IGNORECASE):
            continue
        phrases.append((match.start(), name))
        if re.match(r"\s+is used\b", text[match.end() : match.end() + 24], re.IGNORECASE):
            used.append((match.start(), name))
    found.extend(used or phrases)
    found.sort()
    names: list[str] = []
    for _position, name in found:
        if name not in names:
            names.append(name)
    if "VoxCeleb2" in names and "VoxCeleb" in names:
        names.remove("VoxCeleb")
    if "CelebA-HQ" in names and "CelebA" in names:
        names.remove("CelebA")
    if "VisDrone2019" in names and "VisDrone" in names:
        names.remove("VisDrone")
    return names


def _named_dataset(phrase: str) -> bool:
    tokens = phrase.split()
    words = [token for token in tokens if token.lower() not in {"of", "the", "and", "for"}]
    if not words or len(tokens) > 7:
        return False
    for token in words:
        if len(token) < 2 or token.lower() in SKIP_DATASET_WORDS:
            return False
        parts = token.split("-")
        if len(parts) > 1 and parts[-1][:1].islower():
            return False
    return True


def _metrics(text: str) -> list[tuple[str, str]]:
    found: list[tuple[int, str, str]] = []
    for match in METRIC_BEFORE_RE.finditer(text):
        found.append((match.start(), _metric_name(match.group(3)), _metric_value(match.group(1), match.group(2))))
    for match in METRIC_RE.finditer(text):
        found.append((match.start(), _metric_name(match.group(1)), _metric_value(match.group(2), match.group(3))))
    found.sort()
    kept: list[tuple[str, str]] = []
    seen: set[str] = set()
    for _position, name, value in found:
        if not value or name in seen:
            continue
        seen.add(name)
        kept.append((name, value))
    return kept


def _metric_name(raw: str) -> str:
    name = raw.upper()
    if name == "ACCURACY":
        return "Accuracy"
    if name.startswith("MAP"):
        return "mAP"
    return name


def _metric_value(number: str, unit: str | None) -> str:
    unit = unit or ""
    if "." not in number and unit != "%":
        return ""
    return f"{number}{unit}"


def _limitation(conclusion: str, fallback: str = "") -> str:
    for sentence in _readable_sentences(conclusion):
        if LIMIT_RE.search(sentence):
            return sentence[:400]
    found = _readable_sentences(conclusion)
    if found:
        return found[-1][:400]
    for sentence in _readable_sentences(fallback):
        if LIMIT_RE.search(sentence):
            return sentence[:400]
    return "The paper does not state a limitation."
