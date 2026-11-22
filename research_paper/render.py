"""HTML cards for one paper and for a comparison."""

from __future__ import annotations

import html

from research_paper.compare import Comparison
from research_paper.extract import PaperBrief


def render_page(left: PaperBrief, right: PaperBrief | None, comparison: Comparison | None, note: str) -> str:
    cards = render_brief(left)
    if right is not None:
        cards += render_brief(right)
    compared = render_comparison(comparison) if comparison is not None else ""
    return f"<p class='note'>{html.escape(note)}</p>{cards}{compared}"


def render_brief(brief: PaperBrief) -> str:
    datasets = ", ".join(brief.datasets) or "No dataset name was found."
    if brief.metrics:
        metrics = "".join(f"<li>{html.escape(name)}: {html.escape(value)}</li>" for name, value in brief.metrics)
    else:
        metrics = "<li>No reported number was found.</li>"
    return f"""
<article class="paper-card">
  <p class="kicker">{html.escape(brief.reader)}</p>
  <h3>{html.escape(brief.title)}</h3>
  <p><strong>Problem.</strong> {html.escape(brief.problem)}</p>
  <p><strong>Method.</strong> {html.escape(brief.method)}</p>
  <p><strong>Data.</strong> {html.escape(datasets)}</p>
  <p><strong>Numbers.</strong></p>
  <ul>{metrics}</ul>
  <p><strong>Limit.</strong> {html.escape(brief.limitation)}</p>
</article>
""".strip()


def render_comparison(comparison: Comparison) -> str:
    if comparison.metric_rows:
        rows = "".join(
            "<tr><td>{}</td><td>{}</td><td>{}</td></tr>".format(
                html.escape(name), html.escape(left), html.escape(right)
            )
            for name, left, right in comparison.metric_rows
        )
        table = f"<table><tr><th>Number</th><th>First paper</th><th>Second paper</th></tr>{rows}</table>"
    else:
        table = ""
    shared = ", ".join(comparison.shared_datasets) or "None"
    return f"""
<article class="paper-card compare">
  <p class="kicker">Comparison</p>
  <h3>What the two papers share</h3>
  <p><strong>Shared datasets.</strong> {html.escape(shared)}</p>
  {table}
  <p>{html.escape(comparison.summary)}</p>
</article>
""".strip()
