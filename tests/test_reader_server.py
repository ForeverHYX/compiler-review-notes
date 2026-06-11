import unittest
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


if __name__ == "__main__":
    unittest.main()
