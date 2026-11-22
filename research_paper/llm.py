"""Ask a language model to clean a paper brief. The text reader still works without a key."""

from __future__ import annotations

import json
import os
import urllib.request

from research_paper.extract import PaperBrief

API_URL = "https://api.groq.com/openai/v1/chat/completions"
SYSTEM = (
    "You read computer-vision and generative-model papers. "
    "Return one JSON object with keys title, problem, method, datasets, metrics, limitation. "
    "datasets is a list of dataset names. metrics is a list of objects with name and value. "
    "Use only facts that appear in the paper text. Do not invent numbers."
)


def refine_brief(sections: dict[str, str], fallback: PaperBrief) -> PaperBrief:
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key:
        return fallback
    packed = _pack(sections)
    try:
        payload = _request(key, packed)
    except Exception:
        return fallback
    parsed = _parse(payload)
    if not parsed:
        return fallback
    metrics = []
    for item in parsed.get("metrics") or []:
        if isinstance(item, dict) and item.get("name") and item.get("value"):
            metrics.append((str(item["name"]), str(item["value"])))
    datasets = [str(name) for name in parsed.get("datasets") or [] if str(name).strip()]
    return PaperBrief(
        title=str(parsed.get("title") or fallback.title)[:180],
        problem=str(parsed.get("problem") or fallback.problem)[:500],
        method=str(parsed.get("method") or fallback.method)[:500],
        datasets=datasets or fallback.datasets,
        metrics=metrics or fallback.metrics,
        limitation=str(parsed.get("limitation") or fallback.limitation)[:400],
        reader="language model",
    )


def _pack(sections: dict[str, str]) -> str:
    parts = []
    for name in ("title", "abstract", "method", "experiments", "conclusion"):
        text = sections.get(name, "").strip()
        if text:
            parts.append(f"{name.upper()}\n{text[:1800]}")
    return "\n\n".join(parts)[:7000]


def _request(key: str, paper_text: str) -> str:
    model = os.getenv("GROQ_MODEL", "").strip() or "llama-3.3-70b-versatile"
    body = json.dumps(
        {
            "model": model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": paper_text},
            ],
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=40) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload["choices"][0]["message"]["content"]


def _parse(raw: str) -> dict | None:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.split("\n", 1)[-1]
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        value = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None
