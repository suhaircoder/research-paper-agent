"""Load a paper from a PDF or a text file."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

TEXT_SUFFIXES = {".txt", ".md"}


def load_text(path: str | Path) -> str:
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"Cannot find {file_path.name}.")
    suffix = file_path.suffix.lower()
    if suffix in TEXT_SUFFIXES:
        return file_path.read_text(encoding="utf-8", errors="replace")
    if suffix == ".pdf":
        return _pdf_text(file_path)
    raise ValueError("Upload a PDF or a TXT paper.")


def _pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("Install pypdf to read PDF papers.") from exc
    reader = PdfReader(str(path))
    pages = [(page.extract_text() or "") for page in reader.pages]
    text = "\n".join(pages).strip()
    if _glyphs_are_split(text):
        rebuilt = _text_from_positions(reader).strip()
        if _words_look_real(rebuilt):
            return rebuilt
    if not text:
        raise ValueError("That PDF has no readable text. Export it as text or try another file.")
    return text


def _glyphs_are_split(text: str) -> bool:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) < 30:
        return False
    singles = sum(1 for line in lines if len(line) == 1)
    return singles / len(lines) >= 0.5


def _words_look_real(text: str) -> bool:
    words = [word for word in text.split() if any(character.isalpha() for character in word)]
    if len(words) < 40:
        return False
    average = sum(len(word) for word in words) / len(words)
    return average >= 3


def join_glyphs(glyphs: list[tuple[float, float, str, float, float]]) -> str:
    """Join positioned characters. Each item is y, x, text, advance, font size."""
    lines: dict[float, list[tuple[float, str, float, float]]] = defaultdict(list)
    for y_pos, x_pos, text, advance, size in glyphs:
        if text:
            lines[round(y_pos)].append((x_pos, text, advance, size))
    rows = []
    for y_pos in sorted(lines):
        row = sorted(lines[y_pos])
        pieces: list[str] = []
        for index, (x_pos, text, _advance, _size) in enumerate(row):
            if index:
                prev_x, _prev_text, prev_advance, prev_size = row[index - 1]
                gap = x_pos - (prev_x + prev_advance)
                if gap > max(1.2, prev_size * 0.12):
                    pieces.append(" ")
            pieces.append(text)
        line = "".join(pieces).strip()
        if line:
            rows.append(line)
    return "\n".join(rows)


def _text_from_positions(reader) -> str:
    pages = [_page_from_positions(page) for page in reader.pages]
    return "\n".join(page for page in pages if page)


def _page_from_positions(page) -> str:
    lookup = _font_lookup(page)
    glyphs: list[tuple[float, float, str, float, float]] = []

    def visitor(text, cm, tm, font_dict, font_size):
        if not text or text == "\n":
            return
        matrix, widths = _font_measures(lookup, font_dict)
        size = float(font_size or 0)
        advance = sum(widths.get(character, 500) for character in text) * matrix * size
        glyphs.append((float(tm[5]), float(tm[4]), text, advance, size))

    page.extract_text(visitor_text=visitor)
    return join_glyphs(glyphs)


def _font_lookup(page) -> dict:
    lookup = {}
    resources = page.get("/Resources") or {}
    fonts = resources.get("/Font") or {}
    for ref in fonts.values():
        font = ref.get_object()
        lookup[id(font)] = _font_measures_from(font)
    return lookup


def _font_measures(lookup: dict, font_dict) -> tuple[float, dict[str, float]]:
    if font_dict is None:
        return 0.001, {}
    found = lookup.get(id(font_dict))
    if found:
        return found
    return _font_measures_from(font_dict)


def _font_measures_from(font) -> tuple[float, dict[str, float]]:
    matrix = 0.001
    raw_matrix = font.get("/FontMatrix") if hasattr(font, "get") else None
    if raw_matrix:
        matrix = float(raw_matrix[0]) or 0.001
    widths_list = list(font.get("/Widths") or []) if hasattr(font, "get") else []
    mapping = _unicode_map(font)
    widths = {}
    for code, character in mapping.items():
        if character and code < len(widths_list):
            widths.setdefault(character, float(widths_list[code]))
    return matrix, widths


def _unicode_map(font) -> dict[int, str]:
    mapping: dict[int, str] = {}
    to_unicode = font.get("/ToUnicode") if hasattr(font, "get") else None
    if to_unicode is None:
        return mapping
    data = to_unicode.get_data().decode("latin1", errors="replace")
    mode = ""
    for line in data.splitlines():
        lowered = line.lower()
        if "beginbfchar" in lowered:
            mode = "char"
            continue
        if "beginbfrange" in lowered:
            mode = "range"
            continue
        if "endbfchar" in lowered or "endbfrange" in lowered:
            mode = ""
            continue
        parts = line.strip().split()
        if mode == "char" and len(parts) == 2 and parts[0].startswith("<") and parts[1].startswith("<"):
            mapping[int(parts[0][1:-1], 16)] = chr(int(parts[1][1:-1], 16))
        elif mode == "range" and len(parts) == 3 and all(part.startswith("<") for part in parts):
            start = int(parts[0][1:-1], 16)
            end = int(parts[1][1:-1], 16)
            uni = int(parts[2][1:-1], 16)
            for offset, code in enumerate(range(start, end + 1)):
                mapping[code] = chr(uni + offset)
    return mapping
