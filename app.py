import os

os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")
os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"

import gradio as gr
from dotenv import load_dotenv

from research_paper.library import load_records, notes_markdown, record_from_brief, render_library, save_records
from research_paper.render import render_page
from research_paper.service import analyze_upload, practice_pair

load_dotenv()

THEME = gr.themes.Soft(primary_hue="blue", neutral_hue="stone").set(
    body_background_fill="#f3f1ea",
    block_background_fill="#fffcf7",
    block_border_color="#e3ddd2",
    body_text_color="#1c1915",
    button_primary_background_fill="#1d4e89",
    button_primary_background_fill_hover="#163e6e",
    button_primary_text_color="#ffffff",
)

CSS = """
.gradio-container { max-width: 1080px !important; }
.paper-card {
  background: #fffcf7;
  border: 1px solid #e3ddd2;
  border-left: 6px solid #1d4e89;
  border-radius: 14px;
  padding: 14px 16px;
  margin: 0 0 12px;
}
.paper-card.compare { border-left-color: #8a5a00; }
.kicker { font-size: 12px; letter-spacing: 0.05em; text-transform: uppercase; color: #6d655c; margin: 0; }
.paper-card h3 { font-family: Georgia, "Times New Roman", serif; margin: 4px 0 10px; }
.paper-card p, .paper-card li { color: #1c1915; line-height: 1.45; }
.note { color: #4e483f; }
table { border-collapse: collapse; margin: 8px 0; }
td, th { border: 1px solid #e3ddd2; padding: 6px 8px; text-align: left; }
"""


def _path(upload) -> str:
    if isinstance(upload, (list, tuple)):
        upload = upload[0] if upload else None
    if upload is None:
        return ""
    if isinstance(upload, str):
        return upload
    if isinstance(upload, dict):
        return str(upload.get("path") or "")
    return str(getattr(upload, "name", "") or "")


def _records(left, right) -> list[dict]:
    records = [record_from_brief(left)]
    if right is not None:
        records.append(record_from_brief(right))
    return records


def read_papers(first, second, use_model):
    first_path = _path(first)
    second_path = _path(second)
    if not first_path:
        return "<p class='note'>Upload the first paper. A PDF or TXT file both work.</p>", []
    try:
        left, right, comparison = analyze_upload(first_path, second_path, use_model=bool(use_model))
    except Exception as exc:
        return f"<p class='note'>Could not read that file. {exc}</p>", []
    note = "Read from the paper text."
    if left.reader == "language model" or (right is not None and right.reader == "language model"):
        note = "A language model cleaned the fields. The numbers still come from the paper."
    return render_page(left, right, comparison, note), _records(left, right)


def show_practice():
    left, right, comparison = practice_pair(use_model=False)
    note = "These two write-ups are practice papers, not real publications. They show the card and the comparison."
    return render_page(left, right, comparison, note), _records(left, right)


def save_reading(pending):
    if not pending:
        return "<p class='note'>Read a paper first, then save it.</p>", "No papers are saved yet."
    saved = save_records(list(pending))
    return render_library(saved), notes_markdown(saved)


def show_library():
    saved = load_records()
    return render_library(saved), notes_markdown(saved)


def build_demo() -> gr.Blocks:
    with gr.Blocks(title="Research Paper Agent") as demo:
        gr.Markdown(
            """
# Research Paper Agent
Upload a paper. The agent returns the problem, the method, the dataset, and the numbers. Save each reading to build a library, then copy the notes.
            """.strip()
        )
        with gr.Row():
            with gr.Column():
                first = gr.File(label="First paper", file_types=[".pdf", ".txt"], type="filepath")
                second = gr.File(label="Second paper, optional", file_types=[".pdf", ".txt"], type="filepath")
                use_model = gr.Checkbox(
                    label="Use a language model when GROQ_API_KEY is set",
                    value=False,
                )
                read_button = gr.Button("Read the papers", variant="primary")
                practice_button = gr.Button("Show the practice papers")
                save_button = gr.Button("Save this reading")
                library_button = gr.Button("Show the library")
            results = gr.HTML("<p class='note'>The brief appears here.</p>")
        pending = gr.State([])
        library = gr.HTML("<p class='note'>Saved papers appear here.</p>")
        notes = gr.Textbox(label="Notes you can paste", lines=12)
        read_button.click(read_papers, inputs=[first, second, use_model], outputs=[results, pending])
        practice_button.click(show_practice, outputs=[results, pending])
        save_button.click(save_reading, inputs=pending, outputs=[library, notes])
        library_button.click(show_library, outputs=[library, notes])
    return demo


demo = build_demo()


if __name__ == "__main__":
    demo.launch(
        server_name="127.0.0.1",
        server_port=int(os.getenv("PORT", "7861")),
        inbrowser=False,
        theme=THEME,
        css=CSS,
    )
