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

## 第 04 章补强依据

- 本地 `materials/ch3 语法分析-2(TD).pdf` 前 80 页覆盖：递归下降概述、回溯问题、LL(k)/LL(1) 含义、Nullable/FIRST/FOLLOW 归纳定义与迭代计算、LL(1) 文法定义、预测分析表构造、表项冲突、非递归 table-driven parsing。
- 本地 `materials/ch3 语法分析-2(TD).pdf` 后半部分继续覆盖：表驱动 LL(1) 示例、递归下降代码实现、FIRST/FOLLOW 何时用于选择分支、LL(1) 文法无二义性/无左递归/无左公因子、提左公因子、消除直接左递归、错误恢复目标、空表项报错、insert token 与 delete/skip token 到 FOLLOW 集的取舍。
- 虎书 predictive parsing 小节覆盖：递归下降函数、nullable/FIRST/FOLLOW、Algorithm 3.13、predictive parsing table、LL(1) 含义、左递归消除、提左公因子、error recovery。
- `04_LL1_自顶向下分析.md` 已按教材/PPT顺序补强本章边界、递归下降回溯动机、FIRST 右部串含义、FOLLOW 不含 epsilon、空表项/冲突表项、栈模拟压栈顺序、LL(1) 快速排除性质、错误恢复策略对比和 PPT 覆盖核对。

## 第 05 章补强依据

- 本地 `materials/ch3 语法分析-3(BU)-LR(0)SLR(1).pdf` 共 98 页，PPT 主线包括：LL(1) 局限与 LR(k) 表达力、shift-reduce 分界点模型、最右推导的逆过程、LR 表驱动程序、LR(0) item 表示 RHS 识别进度、LR(0) NFA 直觉、NFA 到 DFA/项集族、closure/goto、从 DFA 填 ACTION/GOTO、状态栈算法、完整 LR(0) 分析示例、LR(0) 中 `0` 的含义、LR(0) 冲突、SLR 用 FOLLOW 集限制 reduce、SLR 仍可能冲突。
- 虎书 LR parsing 小节对应内容包括：状态栈表驱动算法、LR(0) parser generation、closure/goto、增广文法 `S' -> S$`、`$` 不计算 goto 而产生 accept、LR(0) 完整项在所有 token 上 reduce、SLR 只在 FOLLOW 集上填 reduce。
- `05_LR0_SLR_自底向上分析.md` 已按教材/PPT顺序补强本章边界、shift-reduce 分界点与最右推导逆过程、handle/viable prefix、LR(0) item 中 `0` 的含义、LR(0) NFA 到 DFA 直觉、`$`/accept 边界、ACTION/GOTO 填表检查清单、epsilon 规约栈规则、SLR 手算流程、SLR 局限和 PPT 覆盖核对。

## 第 06 章补强依据

- 本地 `materials/ch3 语法分析-4(LR(1), LALR(1), etc).pdf` 共 62 页，PPT 主线包括：SLR 的 FOLLOW 近似局限、LR(1) item 与 lookahead、`FIRST(beta z)` closure、LR(1) goto、LR(1) reduce action、LR(0)/SLR/LR(1) 归约条件对比、LR(1) 状态过多、LALR 合并相同 core、LALR 可能引入 reduce/reduce conflict、Yacc/Bison 作为 LALR parser generator、Lex/Yacc 协作、Yacc 三段式结构、语义动作在 reduce 时执行、优先级/结合性、默认冲突处理、LL/SLR/LR(1) 对比、parser generator 错误恢复、local/global error recovery。
- 虎书 LR parsing/parser generator 小节对应内容包括：LR(1) item 是产生式+点位置+lookahead，起始项 `S' -> .S$` 的额外 lookahead 无关紧要，LR(1) reduce 只填 item 自带 lookahead，LALR 合并 lookahead 不同但 core 相同的状态，Yacc 三段式、shift/reduce 默认 shift、reduce/reduce 默认先出现规则、precedence declarations、`%prec UMINUS`、error token 恢复。
- `06_LR1_LALR_Yacc.md` 已按教材/PPT顺序补强本章边界、SLR FOLLOW 近似局限、LR(1) 起始 lookahead/compact 表示、`FIRST(beta a)` 手算提示、LR(1) 填表规则清单、LALR 合并边和状态、LR 系列方法对比、Yacc 三段式、语义动作执行时机、默认冲突规则、`%left/%right/%nonassoc/%prec`、`error` token 恢复步骤、语法分析方法总览和 PPT 覆盖核对。
