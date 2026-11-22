"""Keep paper briefs on disk and turn them into reading notes."""

from __future__ import annotations

import html
import json
from pathlib import Path

from research_paper.extract import PaperBrief

LIBRARY_PATH = Path(__file__).resolve().parents[1] / "library" / "papers.json"
EMPTY_LIMIT = "The paper does not state a limitation."


def record_from_brief(brief: PaperBrief) -> dict:
    return {
        "title": brief.title,
        "problem": brief.problem,
        "method": brief.method,
        "datasets": list(brief.datasets),
        "metrics": [[name, value] for name, value in brief.metrics],
        "limitation": brief.limitation,
    }


def save_records(records: list[dict], path: Path = LIBRARY_PATH) -> list[dict]:
    stored = load_records(path)
    by_title = {item["title"]: item for item in stored}
    for record in records:
        by_title[record["title"]] = record
    saved = list(by_title.values())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(saved, indent=2), encoding="utf-8")
    return saved


def load_records(path: Path = LIBRARY_PATH) -> list[dict]:
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []


def render_library(records: list[dict]) -> str:
    if not records:
        return "<p class='note'>No papers are saved yet. Read a paper, then save it.</p>"
    rows = []
    for record in records:
        data = ", ".join(record.get("datasets") or []) or "None"
        numbers = ", ".join(f"{name} {value}" for name, value in record.get("metrics") or []) or "None"
        rows.append(
            "<tr><td>{}</td><td>{}</td><td>{}</td></tr>".format(
                html.escape(record.get("title") or "Untitled paper"),
                html.escape(data),
                html.escape(numbers),
            )
        )
    body = "".join(rows)
    return f"""
<article class="paper-card compare">
  <p class="kicker">Library</p>
  <h3>{len(records)} saved papers</h3>
  <table><tr><th>Paper</th><th>Data</th><th>Numbers</th></tr>{body}</table>
</article>
""".strip()


def notes_markdown(records: list[dict]) -> str:
    if not records:
        return "No papers are saved yet."
    blocks = ["# Reading notes", ""]
    for record in records:
        numbers = ", ".join(f"{name} {value}" for name, value in record.get("metrics") or []) or "None"
        data = ", ".join(record.get("datasets") or []) or "None"
        blocks.extend(
            [
                f"## {record.get('title') or 'Untitled paper'}",
                "",
                f"Problem. {record.get('problem') or ''}",
                "",
                f"Method. {record.get('method') or ''}",
                "",
                f"Data. {data}",
                "",
                f"Numbers. {numbers}",
                "",
                f"Limit. {record.get('limitation') or ''}",
                "",
            ]
        )
    blocks.extend(["# Across the papers", "", "| Paper | Data | Numbers |", "| --- | --- | --- |"])
    for record in records:
        data = ", ".join(record.get("datasets") or []) or "None"
        numbers = ", ".join(f"{name} {value}" for name, value in record.get("metrics") or []) or "None"
        title = (record.get("title") or "Untitled paper").replace("|", "/")
        blocks.append(f"| {title} | {data} | {numbers} |")
    limits = [
        f"- {record.get('title')}: {record.get('limitation')}"
        for record in records
        if record.get("limitation") and record.get("limitation") != EMPTY_LIMIT
    ]
    if limits:
        blocks.extend(["", "## Limits", ""])
        blocks.extend(limits)
    return "\n".join(blocks).strip() + "\n"
