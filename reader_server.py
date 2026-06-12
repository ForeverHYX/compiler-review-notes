#!/usr/bin/env python3
"""Local browser reader for the compiler review notes."""

from __future__ import annotations

import argparse
import html
import mimetypes
import re
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote, urlparse


NOTE_RE = re.compile(r"^(\d{2})_.+\.md$")
ANSWER_FILE = "23_练习参考答案.md"
EXCLUDED_MD = {"task_plan.md", "findings.md", "progress.md"}


@dataclass(frozen=True)
class Note:
    number: str
    filename: str
    title: str
    path: Path


@dataclass(frozen=True)
class AnswerIndex:
    chapter_answers: dict[str, str]
    comprehensive_answers: dict[str, dict[int, str]]


def discover_notes(root: Path) -> list[Note]:
    notes: list[Note] = []
    for path in sorted(root.glob("*.md")):
        if path.name in EXCLUDED_MD:
            continue
        match = NOTE_RE.match(path.name)
        if not match:
            continue
        number = match.group(1)
        notes.append(Note(number=number, filename=path.name, title=read_title(path), path=path))
    return notes


def read_title(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def load_answer_index(root: Path) -> AnswerIndex:
    answer_path = root / ANSWER_FILE
    if not answer_path.exists():
        return AnswerIndex(chapter_answers={}, comprehensive_answers={})

    text = answer_path.read_text(encoding="utf-8")
    sections = split_heading_sections(text, level=2)
    chapter_answers: dict[str, str] = {}
    comprehensive_answers: dict[str, dict[int, str]] = {}

    for heading, body in sections:
        match = re.match(r"^##\s+(\d{2})\b", heading)
        if not match:
            continue
        number = match.group(1)
        section_text = f"{heading}\n\n{body}".strip()
        chapter_answers[number] = section_text
        if number == "20":
            comprehensive_answers[number] = split_question_answers(section_text)

    return AnswerIndex(
        chapter_answers=chapter_answers,
        comprehensive_answers=comprehensive_answers,
    )


def split_heading_sections(text: str, level: int) -> list[tuple[str, str]]:
    heading_prefix = "#" * level + " "
    sections: list[tuple[str, list[str]]] = []
    current_heading: str | None = None
    current_lines: list[str] = []

    for line in text.splitlines():
        if line.startswith(heading_prefix):
            if current_heading is not None:
                sections.append((current_heading, current_lines))
            current_heading = line
            current_lines = []
        elif current_heading is not None:
            current_lines.append(line)

    if current_heading is not None:
        sections.append((current_heading, current_lines))

    return [(heading, "\n".join(lines).strip()) for heading, lines in sections]


def split_question_answers(section_text: str) -> dict[int, str]:
    questions: dict[int, str] = {}
    current_number: int | None = None
    current_lines: list[str] = []

    for line in section_text.splitlines():
        match = re.match(r"^###\s+题\s+(\d+)\b", line)
        if match:
            if current_number is not None:
                questions[current_number] = "\n".join(current_lines).strip()
            current_number = int(match.group(1))
            current_lines = [line]
        elif current_number is not None:
            current_lines.append(line)

    if current_number is not None:
        questions[current_number] = "\n".join(current_lines).strip()

    return questions


def normalize_base_path(base_path: str) -> str:
    if not base_path or base_path == "/":
        return ""
    base = "/" + base_path.strip("/")
    return base


def prefixed_path(base_path: str, path: str) -> str:
    base = normalize_base_path(base_path)
    if not path.startswith("/"):
        path = "/" + path
    return base + path


def render_home_page(root: Path, notes: list[Note], answer_index: AnswerIndex, base_path: str = "") -> str:
    base_path = normalize_base_path(base_path)
    material_items = []
    materials_dir = root / "materials"
    if materials_dir.exists():
        for path in sorted(materials_dir.glob("*")):
            if path.is_file():
                href = prefixed_path(base_path, "/materials/" + quote(path.name))
                material_items.append(f'<li><a href="{href}">{html.escape(path.name)}</a></li>')

    note_items = []
    for note in notes:
        href = prefixed_path(base_path, "/note/" + quote(note.filename))
        answer_badge = ""
        if note.number in answer_index.chapter_answers and note.filename != ANSWER_FILE:
            answer_badge = '<span class="badge">答案可展开</span>'
        note_items.append(
            f'<li><a href="{href}"><span>{html.escape(note.filename)}</span>'
            f"<strong>{html.escape(note.title)}</strong></a>{answer_badge}</li>"
        )

    body = f"""
    <section class="hero">
      <p class="eyebrow">Compiler Review Notes</p>
      <h1>编译原理期末复习教程</h1>
      <p>按章节阅读 Markdown 笔记，在练习附近直接展开参考答案。</p>
    </section>
    <section>
      <h2>笔记目录</h2>
      <ol class="note-list">
        {''.join(note_items)}
      </ol>
    </section>
    <section>
      <h2>课程材料</h2>
      <ul class="material-list">
        {''.join(material_items)}
      </ul>
    </section>
    """
    return page_template("编译原理期末复习教程", body, notes, base_path=base_path)


def render_note_page(root: Path, note: Note, answer_index: AnswerIndex, base_path: str = "") -> str:
    base_path = normalize_base_path(base_path)
    markdown = note.path.read_text(encoding="utf-8")
    markdown = inject_answer_drawers(markdown, note, answer_index, base_path=base_path)
    body = f"""
    <article class="note">
      {markdown_to_html(markdown, base_path=base_path)}
    </article>
    """
    return page_template(note.title, body, discover_notes(root), current=note.filename, base_path=base_path)


def inject_answer_drawers(markdown: str, note: Note, answer_index: AnswerIndex, base_path: str = "") -> str:
    if note.filename == ANSWER_FILE:
        return markdown

    if note.number == "20":
        answers = answer_index.comprehensive_answers.get("20", {})
        return inject_comprehensive_answer_drawers(markdown, answers, base_path=base_path)

    answer = answer_index.chapter_answers.get(note.number)
    if not answer:
        return markdown

    drawer = make_answer_drawer(
        key=f"chapter-{note.number}",
        label="显示本章练习参考答案",
        answer_markdown=strip_leading_heading(answer, level=2),
        base_path=base_path,
    )
    pattern = re.compile(
        r"\n##\s+练习参考答案\s*\n+见\s+\[23_练习参考答案\.md\]\(23_练习参考答案\.md\)\s+中对应章节。\s*",
        re.MULTILINE,
    )
    if pattern.search(markdown):
        return pattern.sub("\n" + drawer + "\n", markdown, count=1)

    return markdown + "\n\n" + drawer


def inject_comprehensive_answer_drawers(markdown: str, answers: dict[int, str], base_path: str = "") -> str:
    lines: list[str] = []
    for line in markdown.splitlines():
        lines.append(line)
        match = re.match(r"^###\s+题\s+(\d+)\b", line)
        if not match:
            continue
        number = int(match.group(1))
        answer = answers.get(number)
        if answer:
            lines.append(
                make_answer_drawer(
                    key=f"q-{number}",
                    label=f"显示题 {number} 参考答案",
                    answer_markdown=strip_leading_heading(answer, level=3),
                    base_path=base_path,
                )
            )

    result = "\n".join(lines)
    result = re.sub(
        r"\n##\s+练习参考答案\s*\n+见\s+\[23_练习参考答案\.md\]\(23_练习参考答案\.md\)\s+中对应章节。\s*",
        "\n",
        result,
        count=1,
    )
    return result


def strip_leading_heading(markdown: str, level: int) -> str:
    prefix = "#" * level + " "
    lines = markdown.strip().splitlines()
    if lines and lines[0].startswith(prefix):
        return "\n".join(lines[1:]).strip()
    return markdown.strip()


def make_answer_drawer(key: str, label: str, answer_markdown: str, base_path: str = "") -> str:
    answer_html = markdown_to_html(answer_markdown, base_path=base_path)
    return (
        f'<details class="answer-drawer" data-answer-key="{html.escape(key)}">'
        f"<summary>{html.escape(label)}</summary>"
        f'<div class="answer-content">{answer_html}</div>'
        "</details>"
    )


def markdown_to_html(markdown: str, base_path: str = "") -> str:
    lines = markdown.splitlines()
    blocks: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]

        if not line.strip():
            index += 1
            continue

        if line.startswith("<"):
            raw_lines = [line]
            index += 1
            while index < len(lines) and lines[index].startswith("<"):
                raw_lines.append(lines[index])
                index += 1
            blocks.append("\n".join(raw_lines))
            continue

        if line.startswith("```"):
            info = html.escape(line[3:].strip())
            code_lines: list[str] = []
            index += 1
            while index < len(lines) and not lines[index].startswith("```"):
                code_lines.append(lines[index])
                index += 1
            if index < len(lines):
                index += 1
            class_attr = f' class="language-{info}"' if info else ""
            blocks.append(f"<pre><code{class_attr}>{html.escape(chr(10).join(code_lines))}</code></pre>")
            continue

        if is_table_start(lines, index):
            table_lines = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                table_lines.append(lines[index])
                index += 1
            blocks.append(render_table(table_lines, base_path=base_path))
            continue

        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading:
            level = len(heading.group(1))
            text = heading.group(2).strip()
            anchor = slugify(text)
            blocks.append(f'<h{level} id="{anchor}">{render_inline(text, base_path=base_path)}</h{level}>')
            index += 1
            continue

        unordered = re.match(r"^\s*[-*]\s+(.+)$", line)
        if unordered:
            items: list[str] = []
            while index < len(lines):
                item = re.match(r"^\s*[-*]\s+(.+)$", lines[index])
                if not item:
                    break
                items.append(f"<li>{render_inline(item.group(1).strip(), base_path=base_path)}</li>")
                index += 1
            blocks.append("<ul>" + "".join(items) + "</ul>")
            continue

        ordered = re.match(r"^\s*\d+\.\s+(.+)$", line)
        if ordered:
            items = []
            while index < len(lines):
                item = re.match(r"^\s*\d+\.\s+(.+)$", lines[index])
                if not item:
                    break
                items.append(f"<li>{render_inline(item.group(1).strip(), base_path=base_path)}</li>")
                index += 1
            blocks.append("<ol>" + "".join(items) + "</ol>")
            continue

        paragraph_lines = [line.strip()]
        index += 1
        while index < len(lines) and lines[index].strip():
            next_line = lines[index]
            if (
                next_line.startswith("```")
                or next_line.startswith("<")
                or next_line.startswith("#")
                or re.match(r"^\s*([-*]|\d+\.)\s+", next_line)
                or is_table_start(lines, index)
            ):
                break
            paragraph_lines.append(next_line.strip())
            index += 1
        blocks.append(f"<p>{render_inline(' '.join(paragraph_lines), base_path=base_path)}</p>")

    return "\n".join(blocks)


def is_table_start(lines: list[str], index: int) -> bool:
    if index + 1 >= len(lines):
        return False
    return lines[index].strip().startswith("|") and re.match(r"^\s*\|?\s*:?-{3,}:?\s*\|", lines[index + 1]) is not None


def render_table(table_lines: list[str], base_path: str = "") -> str:
    rows = [split_table_row(line) for line in table_lines if line.strip()]
    if len(rows) < 2:
        return "<p>" + render_inline(" ".join(table_lines), base_path=base_path) + "</p>"

    header = rows[0]
    body_rows = rows[2:]
    thead = "<thead><tr>" + "".join(f"<th>{render_inline(cell, base_path=base_path)}</th>" for cell in header) + "</tr></thead>"
    tbody = "<tbody>" + "".join(
        "<tr>" + "".join(f"<td>{render_inline(cell, base_path=base_path)}</td>" for cell in row) + "</tr>"
        for row in body_rows
    ) + "</tbody>"
    return f"<table>{thead}{tbody}</table>"


def split_table_row(line: str) -> list[str]:
    text = line.strip()
    cells: list[str] = []
    current: list[str] = []
    code_tick_run = 0
    index = 0

    while index < len(text):
        char = text[index]

        if char == "\\" and code_tick_run == 0 and index + 1 < len(text) and text[index + 1] == "|":
            current.append("|")
            index += 2
            continue

        if char == "`":
            run_length = count_backtick_run(text, index)
            current.append("`" * run_length)
            if code_tick_run == 0:
                code_tick_run = run_length
            elif code_tick_run == run_length:
                code_tick_run = 0
            index += run_length
            continue

        if char == "|" and code_tick_run == 0:
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
        index += 1

    cells.append("".join(current).strip())
    if cells and cells[0] == "":
        cells = cells[1:]
    if cells and cells[-1] == "":
        cells = cells[:-1]
    return cells


def render_inline(text: str, base_path: str = "") -> str:
    escaped, code_spans = extract_code_spans(text)

    def link_repl(match: re.Match[str]) -> str:
        label = match.group(1)
        target = html.unescape(match.group(2))
        href = target
        if target.endswith(".md"):
            href = prefixed_path(base_path, "/note/" + quote(target))
        elif target.endswith(".pdf") or target.startswith("materials/"):
            href = prefixed_path(base_path, "/" + quote(target, safe="/"))
        return f'<a href="{html.escape(href)}">{label}</a>'

    escaped = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link_repl, escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    for placeholder, code_html in code_spans:
        escaped = escaped.replace(placeholder, code_html)
    return escaped


def count_backtick_run(text: str, start: int) -> int:
    index = start
    while index < len(text) and text[index] == "`":
        index += 1
    return index - start


def extract_code_spans(text: str) -> tuple[str, list[tuple[str, str]]]:
    pieces: list[str] = []
    buffer: list[str] = []
    code_spans: list[tuple[str, str]] = []
    index = 0

    def flush_buffer() -> None:
        if buffer:
            pieces.append(html.escape("".join(buffer)))
            buffer.clear()

    while index < len(text):
        if text[index] == "`":
            run_length = count_backtick_run(text, index)
            close = text.find("`" * run_length, index + run_length)
            if close != -1:
                flush_buffer()
                content = text[index + run_length : close]
                placeholder = f"\x00CODE{len(code_spans)}\x00"
                code_spans.append((placeholder, f"<code>{html.escape(content)}</code>"))
                pieces.append(placeholder)
                index = close + run_length
                continue
        buffer.append(text[index])
        index += 1

    flush_buffer()
    return "".join(pieces), code_spans


def slugify(text: str) -> str:
    slug = re.sub(r"\s+", "-", text.strip().lower())
    slug = re.sub(r"[^\w\-\u4e00-\u9fff]+", "", slug)
    return quote(slug or "section")


def page_template(title: str, body: str, notes: list[Note], current: str | None = None, base_path: str = "") -> str:
    base_path = normalize_base_path(base_path)
    nav_links = []
    for note in notes:
        active = " active" if note.filename == current else ""
        nav_links.append(
            f'<a class="nav-link{active}" href="{prefixed_path(base_path, "/note/" + quote(note.filename))}">'
            f'<span>{html.escape(note.number)}</span>{html.escape(note.title)}</a>'
        )

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f7f7f4;
      --panel: #ffffff;
      --ink: #202124;
      --muted: #666b73;
      --line: #d9ded6;
      --accent: #126a72;
      --accent-soft: #e4f1f1;
      --code: #22272e;
      --warn: #9f4d00;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans CJK SC", "PingFang SC", sans-serif;
      line-height: 1.72;
      color: var(--ink);
      background: var(--bg);
    }}
    a {{ color: var(--accent); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .layout {{ display: grid; grid-template-columns: minmax(230px, 18vw) minmax(0, 1fr); min-height: 100vh; }}
    aside {{
      position: sticky;
      top: 0;
      height: 100vh;
      overflow: auto;
      border-right: 1px solid var(--line);
      background: #fbfbf8;
      padding: 18px 14px;
    }}
    .brand {{ display: block; font-weight: 750; color: var(--ink); margin-bottom: 14px; }}
    .nav-link {{
      display: grid;
      grid-template-columns: 34px minmax(0, 1fr);
      gap: 8px;
      align-items: start;
      padding: 8px;
      border-radius: 6px;
      color: var(--ink);
      font-size: 14px;
      line-height: 1.35;
    }}
    .nav-link span {{ color: var(--muted); font-variant-numeric: tabular-nums; }}
    .nav-link.active {{ background: var(--accent-soft); color: var(--accent); font-weight: 700; }}
    main {{ max-width: 1120px; width: 100%; padding: 36px clamp(18px, 4vw, 56px) 72px; }}
    .hero {{
      padding: clamp(28px, 6vw, 72px) 0 26px;
      border-bottom: 1px solid var(--line);
      margin-bottom: 26px;
    }}
    .eyebrow {{ color: var(--accent); font-weight: 700; letter-spacing: 0; text-transform: uppercase; font-size: 13px; }}
    h1, h2, h3, h4 {{ line-height: 1.25; margin: 1.6em 0 0.55em; }}
    h1 {{ font-size: clamp(30px, 4vw, 48px); margin-top: 0; }}
    h2 {{ font-size: 26px; border-top: 1px solid var(--line); padding-top: 22px; }}
    h3 {{ font-size: 21px; }}
    h4 {{ font-size: 17px; }}
    p, ul, ol, table, pre, details {{ margin: 0 0 16px; }}
    li {{ margin: 4px 0; }}
    code {{
      font-family: "SFMono-Regular", Consolas, monospace;
      background: #eef1ee;
      border: 1px solid #dfe4df;
      border-radius: 4px;
      padding: 0.08em 0.28em;
      font-size: 0.92em;
    }}
    pre {{
      overflow: auto;
      padding: 14px 16px;
      border-radius: 8px;
      background: var(--code);
      color: #f2f4f8;
      line-height: 1.55;
    }}
    pre code {{ background: transparent; border: 0; color: inherit; padding: 0; }}
    table {{ width: 100%; border-collapse: collapse; background: var(--panel); }}
    th, td {{ border: 1px solid var(--line); padding: 8px 10px; vertical-align: top; }}
    th {{ background: #eef3ed; text-align: left; }}
    .note-list {{ padding-left: 0; list-style: none; display: grid; gap: 8px; }}
    .note-list li {{ display: flex; gap: 10px; align-items: center; background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 10px 12px; }}
    .note-list a {{ display: grid; gap: 2px; color: var(--ink); flex: 1; }}
    .note-list a span {{ color: var(--muted); font-size: 13px; }}
    .badge {{ color: var(--warn); background: #fff2df; border: 1px solid #f0d0a3; border-radius: 999px; padding: 2px 8px; font-size: 12px; white-space: nowrap; }}
    .material-list {{ columns: 2; }}
    .answer-drawer {{
      border: 1px solid #cbdedb;
      border-radius: 8px;
      background: #f5fbfa;
      padding: 0;
      overflow: hidden;
    }}
    .answer-drawer summary {{
      cursor: pointer;
      color: var(--accent);
      font-weight: 750;
      padding: 12px 14px;
      background: var(--accent-soft);
    }}
    .answer-content {{ padding: 14px; }}
    .answer-content h1, .answer-content h2, .answer-content h3 {{ margin-top: 0.4em; border-top: 0; padding-top: 0; }}
    @media (max-width: 860px) {{
      .layout {{ display: block; }}
      aside {{ position: static; height: auto; max-height: 42vh; border-right: 0; border-bottom: 1px solid var(--line); }}
      main {{ padding-top: 24px; }}
      .material-list {{ columns: 1; }}
    }}
  </style>
</head>
<body>
  <div class="layout">
    <aside>
      <a class="brand" href="{prefixed_path(base_path, "/")}">编译原理复习</a>
      <nav>{''.join(nav_links)}</nav>
    </aside>
    <main>{body}</main>
  </div>
</body>
</html>"""


class ReaderRequestHandler(BaseHTTPRequestHandler):
    root: Path
    base_path: str = ""

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = self.strip_base_path(parsed.path)
        if path is None:
            self.send_error(404, "not found")
            return
        try:
            if path == "/":
                self.respond_html(
                    render_home_page(
                        self.root,
                        discover_notes(self.root),
                        load_answer_index(self.root),
                        base_path=self.base_path,
                    )
                )
                return
            if path.startswith("/note/"):
                filename = unquote(path.removeprefix("/note/"))
                note = self.find_note(filename)
                if note is None:
                    self.send_error(404, "note not found")
                    return
                self.respond_html(render_note_page(self.root, note, load_answer_index(self.root), base_path=self.base_path))
                return
            if path.startswith("/materials/"):
                filename = unquote(path.removeprefix("/materials/"))
                self.respond_file(self.root / "materials" / filename)
                return
            self.send_error(404, "not found")
        except OSError as exc:
            self.send_error(500, str(exc))

    def strip_base_path(self, request_path: str) -> str | None:
        base = normalize_base_path(self.base_path)
        if not base:
            return request_path
        if request_path == base:
            return "/"
        if request_path.startswith(base + "/"):
            stripped = request_path[len(base):]
            return stripped or "/"
        return None

    def find_note(self, filename: str) -> Note | None:
        for note in discover_notes(self.root):
            if note.filename == filename:
                return note
        return None

    def respond_html(self, content: str) -> None:
        data = content.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def respond_file(self, path: Path) -> None:
        root_materials = (self.root / "materials").resolve()
        resolved = path.resolve()
        if root_materials not in resolved.parents and resolved != root_materials:
            self.send_error(403, "forbidden")
            return
        if not resolved.exists() or not resolved.is_file():
            self.send_error(404, "file not found")
            return
        mime, _ = mimetypes.guess_type(str(resolved))
        data = resolved.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mime or "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.address_string()} - {format % args}")


def run_server(root: Path, host: str, port: int, base_path: str = "") -> None:
    handler = type(
        "ConfiguredReaderRequestHandler",
        (ReaderRequestHandler,),
        {"root": root.resolve(), "base_path": normalize_base_path(base_path)},
    )
    server = ThreadingHTTPServer((host, port), handler)
    path = normalize_base_path(base_path) or "/"
    print(f"Serving compiler review notes at http://{host}:{port}{path}")
    server.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve compiler review notes in a browser.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--base-path", default="")
    args = parser.parse_args()
    run_server(args.root, args.host, args.port, base_path=args.base_path)


if __name__ == "__main__":
    main()
