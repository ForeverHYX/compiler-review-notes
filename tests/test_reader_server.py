import unittest
import re
from pathlib import Path

import reader_server


ROOT = Path(__file__).resolve().parents[1]


class ReaderServerTests(unittest.TestCase):
    def test_discovers_ordered_note_files_without_plan_files(self):
        notes = reader_server.discover_notes(ROOT)

        names = [note.filename for note in notes]
        self.assertIn("00_复习路线与课程覆盖.md", names)
        self.assertIn("24_回忆卷解析与考点加固.md", names)
        self.assertNotIn("task_plan.md", names)
        self.assertIn("23_练习参考答案.md", names)
        self.assertEqual(names, sorted(names))

    def test_answer_index_maps_chapters_and_comprehensive_questions(self):
        index = reader_server.load_answer_index(ROOT)

        self.assertIn("02", index.chapter_answers)
        self.assertIn("最长匹配", index.chapter_answers["02"])
        self.assertIn("20", index.comprehensive_answers)
        self.assertIn(1, index.comprehensive_answers["20"])
        self.assertIn("ifx", index.comprehensive_answers["20"][1])

    def test_note_rendering_includes_local_answer_drawer(self):
        index = reader_server.load_answer_index(ROOT)
        note = next(note for note in reader_server.discover_notes(ROOT) if note.number == "02")

        html = reader_server.render_note_page(ROOT, note, index)

        self.assertIn("data-answer-key=\"chapter-02\"", html)
        self.assertIn("显示本章练习参考答案", html)
        self.assertIn("最长匹配", html)
        self.assertNotIn("href=\"23_练习参考答案.md\"", html)

    def test_comprehensive_page_has_per_question_answer_buttons(self):
        index = reader_server.load_answer_index(ROOT)
        note = next(note for note in reader_server.discover_notes(ROOT) if note.number == "20")

        html = reader_server.render_note_page(ROOT, note, index)

        self.assertIn("data-answer-key=\"q-1\"", html)
        self.assertIn("显示题 1 参考答案", html)

    def test_home_page_lists_notes_and_materials(self):
        notes = reader_server.discover_notes(ROOT)
        index = reader_server.load_answer_index(ROOT)

        html = reader_server.render_home_page(ROOT, notes, index)

        self.assertIn("编译原理期末复习教程", html)
        self.assertIn("02_词法分析_RE_NFA_DFA_Lex.md", html)
        self.assertIn("ch18 循环优化.pdf", html)

    def test_pages_load_mathjax_for_latex_notation(self):
        notes = reader_server.discover_notes(ROOT)
        index = reader_server.load_answer_index(ROOT)

        html = reader_server.render_home_page(ROOT, notes, index)

        self.assertIn("window.MathJax", html)
        self.assertIn("tex-mml-chtml.js", html)

    def test_base_path_prefixes_reader_links(self):
        notes = reader_server.discover_notes(ROOT)
        index = reader_server.load_answer_index(ROOT)

        html = reader_server.render_home_page(ROOT, notes, index, base_path="/compiler-notes")

        self.assertIn("/compiler-notes/note/02_", html)
        self.assertIn("/compiler-notes/materials/ch18", html)

    def test_base_path_prefixes_markdown_links(self):
        html = reader_server.markdown_to_html(
            "见 [答案](23_练习参考答案.md) 和 [材料](materials/ch18 循环优化.pdf)",
            base_path="/compiler-notes",
        )

        self.assertIn('href="/compiler-notes/note/23_', html)
        self.assertIn('href="/compiler-notes/materials/ch18', html)

    def test_base_path_prefixes_table_links(self):
        html = reader_server.markdown_to_html(
            "| 文件 | 内容 |\n|---|---|\n| [答案](23_练习参考答案.md) | ok |",
            base_path="/compiler-notes",
        )

        self.assertIn('href="/compiler-notes/note/23_', html)

    def test_multiline_svg_html_block_is_preserved(self):
        html = reader_server.markdown_to_html(
            '<figure class="svg-diagram">\n'
            '  <svg viewBox="0 0 120 40" role="img" aria-labelledby="t">\n'
            "    <title id=\"t\">示意图</title>\n"
            '    <path d="M10 20 H110" />\n'
            "  </svg>\n"
            "</figure>"
        )

        self.assertIn('<figure class="svg-diagram">', html)
        self.assertIn('<svg viewBox="0 0 120 40"', html)
        self.assertIn('<path d="M10 20 H110" />', html)
        self.assertNotIn("&lt;svg", html)

    def test_markdown_inside_details_blocks_is_rendered(self):
        html = reader_server.markdown_to_html(
            '<details class="answer-drawer">\n'
            "<summary>答案与解析</summary>\n"
            "\n"
            "**答案：True**\n"
            "\n"
            "```text\n"
            "x <- 1\n"
            "```\n"
            "\n"
            "</details>"
        )

        self.assertIn('<details class="answer-drawer">', html)
        self.assertIn("<strong>答案：True</strong>", html)
        self.assertIn('<pre><code class="language-text">x &lt;- 1</code></pre>', html)
        self.assertNotIn("**答案：True**", html)

    def test_indented_fenced_code_blocks_render_without_raw_ticks(self):
        html = reader_server.markdown_to_html(
            "1. 构造项集时必须先增广：\n"
            "   ```text\n"
            "   S' -> . S EOF\n"
            "   ```\n"
            "   完整项集族如下。"
        )

        self.assertIn("<ol><li>构造项集时必须先增广：</li></ol>", html)
        self.assertIn(
            '<pre><code class="language-text">S&#x27; -&gt; . S EOF</code></pre>',
            html,
        )
        self.assertIn("<p>完整项集族如下。</p>", html)
        self.assertNotIn("```text", html)

    def test_table_cells_preserve_pipes_inside_inline_code(self):
        html = reader_server.markdown_to_html(
            "| 正则 | 含义 |\n"
            "|---|---|\n"
            "| `r | s` | 并集 |\n"
            "| a\\|b | escaped pipe |"
        )

        self.assertIn("<td><code>r | s</code></td><td>并集</td>", html)
        self.assertIn("<td>a|b</td><td>escaped pipe</td>", html)
        self.assertNotIn("<td>`r</td>", html)

    def test_double_backtick_inline_code_renders_as_one_code_span(self):
        html = reader_server.markdown_to_html("占位符 `` `d0`` 表示第 0 个 destination temp。")

        self.assertIn("<code> `d0</code>", html)
        self.assertNotIn("<code> </code>d0", html)

    def test_ordered_lists_preserve_explicit_start_after_block_breaks(self):
        html = reader_server.markdown_to_html("1. 第一题\n\n中间解释段落。\n\n2. 第二题")

        self.assertIn("<ol><li>第一题</li></ol>", html)
        self.assertIn('<ol start="2"><li>第二题</li></ol>', html)

    def test_rendered_note_tables_have_consistent_column_counts(self):
        answer_index = reader_server.load_answer_index(ROOT)

        for note in reader_server.discover_notes(ROOT):
            with self.subTest(note=note.filename):
                html = reader_server.render_note_page(ROOT, note, answer_index)
                for table in re.findall(r"<table>.*?</table>", html, flags=re.S):
                    header_count = table.count("<th>")
                    self.assertGreater(header_count, 0)
                    for row in re.findall(r"<tr>(.*?)</tr>", table, flags=re.S):
                        body_count = row.count("<td>")
                        if body_count:
                            self.assertEqual(body_count, header_count, row[:240])


if __name__ == "__main__":
    unittest.main()
