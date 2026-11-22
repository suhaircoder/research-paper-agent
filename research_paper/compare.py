"""Compare two paper briefs on data, numbers, and method."""

from __future__ import annotations

from dataclasses import dataclass

from research_paper.extract import PaperBrief


@dataclass
class Comparison:
    shared_datasets: list[str]
    metric_rows: list[tuple[str, str, str]]
    summary: str


def compare_briefs(left: PaperBrief, right: PaperBrief) -> Comparison:
    shared = [name for name in left.datasets if name in right.datasets]
    right_metrics = dict(right.metrics)
    rows = [
        (name, value, right_metrics[name])
        for name, value in left.metrics
        if name in right_metrics
    ]
    lines = [_dataset_line(left, right, shared), _metric_line(left, right, rows)]
    lines.append(f"{left.title} — {left.method}")
    lines.append(f"{right.title} — {right.method}")
    return Comparison(shared_datasets=shared, metric_rows=rows, summary=" ".join(lines))


def _dataset_line(left: PaperBrief, right: PaperBrief, shared: list[str]) -> str:
    if shared:
        return "Both papers use " + ", ".join(shared) + "."
    left_data = ", ".join(left.datasets) or "no named dataset"
    right_data = ", ".join(right.datasets) or "no named dataset"
    return f"They use different data: {left_data} on the first paper, and {right_data} on the second."


def _metric_line(left: PaperBrief, right: PaperBrief, rows: list[tuple[str, str, str]]) -> str:
    if rows:
        pieces = [f"{name} is {left_value} versus {right_value}" for name, left_value, right_value in rows]
        return "Shared numbers: " + "; ".join(pieces) + "."
    left_numbers = ", ".join(f"{name} {value}" for name, value in left.metrics) or "no reported number"
    right_numbers = ", ".join(f"{name} {value}" for name, value in right.metrics) or "no reported number"
    return f"They do not report the same number. First paper: {left_numbers}. Second paper: {right_numbers}."
