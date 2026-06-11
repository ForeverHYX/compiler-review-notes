# 编译原理复习笔记发现记录

## 仓库现状

- 根目录已有 `00` 到 `24` 共 25 个 Markdown 复习文件，以及 `README.md`。
- `materials/` 包含课程 PPT 和虎书 PDF；`materials/README.md` 当前列到 ch14，未列出已存在的 `ch18 循环优化.pdf`。
- 已新增 `reader_server.py` 和 `tests/test_reader_server.py`，实现无外部依赖的本地阅读器与单元测试。
- `22_覆盖审计与补强说明.md` 已记录：主线为 ch1-ch14 和 ch18，ch15-ch17/ch19-ch21 作为拓展速读。
- `23_练习参考答案.md` 已集中放置参考答案；浏览器阅读器需要把这些答案映射到对应练习位置，提供就地展开。
- 阅读器可用 Python 标准库实现，避免引入联网依赖；需要自带简化 Markdown 渲染，覆盖标题、段落、列表、代码块、表格、链接和行内代码。

## 工作区状态

- `02_词法分析_RE_NFA_DFA_Lex.md` 原先在 `id = letter (letter | digit)*` 附近的 `=` 和空行残留已修正，并在同章完成初学者向扩充。
- `materials/ch18 循环优化.pdf` 是未跟踪文件，但与目标一致，应在材料清单和覆盖审计中纳入。

## 待进一步审计

- 需要抽查每个课件 PDF 的目录/页标题，确认现有章节覆盖所有 PPT 小节。
- 需要抽查虎书目录中未在 PPT 主线出现的章节，确认 `19_教材后半拓展速读.md` 是否足够“略微介绍”。
- 需要确认答案文件的标题结构，便于阅读器自动把答案绑定回题目。
- `23_练习参考答案.md` 的章节答案使用 `## 01` 到 `## 20`；综合练习题答案在 `## 20 综合练习题` 下继续用 `### 题 N` 分题。

## 第 02 章补强依据

- 本地 `materials/ch2 词法分析.pdf` 共 107 页，PPT 主线包括：词法分析概述、形式语言、正则表达式、有穷自动机、词法分析器自动生成、Lex 工具。
- 虎书目录显示第 2 章小节为 lexical tokens、regular expressions、finite automata、nondeterministic finite automata、Lex。
- Flex 官方手册说明 scanner 会选择匹配最多文本的规则，同长度时选择 flex 输入文件中靠前的规则：<https://westes.github.io/flex/manual/Matching.html>
- Crafting Interpreters 的 scanning 章节强调 scanner 从字符流分组 lexeme，并把 token 类型、literal value、位置等信息打包成 token 对象：<https://craftinginterpreters.com/scanning.html>
- chibicc 的 `tokenize.c` 展示真实手写 C lexer 会跳过注释/空白、识别数字/字符串/identifier/punctuator，再把 identifier 中的关键字转换为 keyword：<https://github.com/rui314/chibicc/blob/main/tokenize.c>
