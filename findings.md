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

## 第 03 章补强依据

- 本地 `materials/ch3 语法分析-1(CFG和Parsing概述).pdf` 共 79 页，PPT 主线包括：语法分析器作用、CFG 四元组、Tiger 直线程序语法、EOF augmented grammar、推导/归约、最左/最右推导、sentential form/sentence/language、parse tree、parsing 作为搜索问题、top-down/bottom-up、正则语言 vs CFG、二义性、表达式分层消除二义性、dangling else、Yacc 的优先级/结合性声明。
- 虎书第 3 章目录显示 parsing 包括 context-free grammars、predictive parsing、LR parsing、parser generators、error recovery；第 03 章应先把 CFG/parse tree/ambiguity 铺扎实，后续 04-06 再讲具体算法。
- Crafting Interpreters 的 “Representing Code” 章节用 `1 + 2 * 3 - 4` 和语法树说明“parser 把 token 流转换为更丰富的树结构”，也强调 syntactic grammar 的 alphabet 是 token 而不是 character：<https://craftinginterpreters.com/representing-code.html>
- GNU Bison 手册的 shift/reduce conflict 页面说明 dangling else 的冲突本质：读到 `else` 时既可 reduce 又可 shift；Bison 默认 shift，因此 `else` 绑定到最近的未匹配 `if`：<https://www.gnu.org/software/bison/manual/html_node/Shift_002fReduce.html>
- GNU Bison 手册 operator precedence 页面说明算术表达式也会产生 shift/reduce conflict，工具可用 precedence declarations 决定 shift/reduce：<https://www.gnu.org/software/bison/manual/html_node/Precedence.html>
