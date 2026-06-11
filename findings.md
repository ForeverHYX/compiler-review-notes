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

## 第 07 章补强依据

- 本地 `materials/ch4 抽象语法.pdf` 共 48 页，PPT 主线包括：lexer/parser recap、属性文法只需理解思想、语义动作与 semantic value、递归下降和 Yacc 中的语义动作、语义值栈、不要把整个编译器塞进 parser action、parse tree 的冗余与文法依赖、AST 作为 parser 和后续阶段的 clean interface、AST 应用、C tagged union/Java class/F# ADT 表示、tree-walking 操作、top-down/bottom-up 构造 AST、位置 position 字段、position stack 或 Yacc `pos` 非终结符技巧。
- 虎书 Abstract Syntax 章节对应内容包括：semantic actions、Yacc semantic stack、parse tree/concrete syntax 与 abstract syntax、AST 让后续语义分析不受文法改写干扰、Tiger `absyn.h` 构造函数、`A_var/A_exp/A_dec/A_ty` 分类、`A_pos` 字段、连续 function/type declarations 合并为同一个 `FunctionDec/TypeDec`、`&`/`|`/unary minus 可翻译为已有 AST 节点、`S_symbol`、`escape` 字段。
- `07_AST_抽象语法.md` 已按教材/PPT顺序补强本章边界、属性文法考试深度、parse tree 与 AST 的接口意义、为什么不在 parser action 里做完整编译、top-down/bottom-up 构造方式对比、Tiger 连续函数/类型声明合并、`&`/`|`/一元负号的 AST 表示、`S_symbol`/`escape`、position stack/Yacc `pos` 技巧、语义值栈规则和 PPT 覆盖核对。

## 第 08 章补强依据

- 本地 `materials/ch5 语义分析.pdf` 共 93 页，PPT 主线包括：CFG/parsing 的局限、广义/狭义 semantic analysis、binding/environment/symbol table、作用域和 shadowing、多个符号表、`insert/lookup/beginScope/endScope` 接口、imperative 与 functional 符号表、单一 hash table 加 scope marker、string 到 symbol 的实现技巧、type system 基本概念、Tiger 的 TEnv/VEnv、Tiger 类型、name equivalence、递归类型、nil、无隐式转换、typing judgment、递归 type checker、`transExp/transVar/transDec/transTy`、变量/类型/函数声明检查、递归类型/函数声明 two-pass。
- 虎书 Semantic Analysis 章节对应内容包括：语义分析连接定义和使用、检查表达式类型并准备 IR；symbol table/environment；多个 active environments；外部链哈希表与 `S_beginScope/S_endScope`；functional-style symbol table；`S_symbol` interning；Tiger `Ty_ty`、`E_varEntry/E_funEntry`、`base_tenv/base_venv`；`actual_ty`；`transVar` 简单变量查 `VarEntry`；`LetExp` 同时打开 `venv/tenv`；变量声明中 `nil` initializer 需要 record 约束；函数声明参数作用域和返回类型检查；递归 type/function 声明先登记 header 再检查 body。
- Princeton 公开的 Modern Compiler Implementation in C 项目页提供了虎书相关源文件入口，`types.h` 中的 `Ty_record/Ty_nil/Ty_int/Ty_string/Ty_array/Ty_name/Ty_void` 与本章 Tiger 类型表示一致：<https://www.cs.princeton.edu/~appel/modern/c/>
- `08_语义分析_符号表_类型检查.md` 已按教材/PPT顺序补强本章边界、广义/狭义语义分析、多符号表与 TEnv/VEnv、三类符号表实现、external chaining 判断题陷阱、string interning、Tiger type system、形式化记号阅读深度、`actual_ty`、`transVar` 三类变量访问、`transDec` 声明检查、作用域大题模板和 PPT 覆盖核对。

## 第 09 章补强依据

- 本地 `materials/ch6 活动记录.pdf` 共 53 页，PPT 主线包括：run-time environment 中 code/data 的划分、现代处理器寄存器/内存直觉、运行时内存布局、activation record/stack frame、递归调用中每次调用有独立参数和局部变量、globals/static data、heap 中动态对象、FP/SP、寄存器减少栈帧内存流量、Tiger call-by-value、参数寄存器、caller-save/callee-save、return address、return value、locals/temporaries、frame-resident variables 的七个原因、escape variables 和总结。
- 本地 `materials/ch6 活动记录2（Block).pdf` 共 57 页，PPT 主线包括：nested functions 的 block structure 问题、static link、display、lambda lifting 三种实现策略、static link 访问非局部变量、static link 与 dynamic link 对比、display 的维护、三种方案对比、Tiger 典型栈帧布局、static link 可能跳过 dynamic frames、stack frame 对 higher-order functions 的限制，以及 prettyprint 示例中的 static link 设置公式。
- 虎书 Activation Records 章节对应内容包括：局部变量 LIFO 生命周期、higher-order functions 需要 closure 而不能只靠 stack frame、stack pointer/frame pointer、stack frame 图、caller-save/callee-save 是 calling convention、参数寄存器带来的保存问题、frame-resident 条件、escape 定义、FindEscape 必须早于 Semant、`F_frame/F_access/F_newFrame/F_allocLocal`、`InFrame/InReg`、view shift、`Tr_level/Tr_access` 两层抽象、static link 由 Translate 处理并作为隐藏 formal 加入 frame。
- x86-64 psABI GitLab 项目提供 System V AMD64 ABI 的官方维护入口；其公开说明与本章调用约定补充相关：<https://gitlab.com/x86-psABIs/x86-64-ABI/-/raw/master/README.md>。实际考试仍以 PPT 中的抽象 calling convention 和虎书 Frame 模块为准。

## 第 10 章补强依据

- 本地 `materials/ch7 中间表示生成.pdf` 共 81 页，PPT 主线包括：IR 在前端/中端/后端之间的作用、IR 按抽象层次和结构分类、三地址码、Tiger 的 IR Tree、IR Tree expression/statement 节点定义、`MEM` 和 `ESEQ` 语义、`NAME` 与 `LABEL` 区别、Ex/Nx/Cx、形态转换、simple variable 和 static link 访问、Tiger array/record 变量是指针、l-value/r-value、structured l-value、array subscript 与 field selection、arithmetic、conditionals、short-circuit、while/break、for 避免 `maxint` 溢出、function call hidden static link、variable/type/function declaration、prologue/body/epilogue、key design decisions。
- 虎书 Translation to Intermediate Code 章节对应内容包括：`tree.h` 中 `T_exp/T_stm` 节点、无限 temporary、`MEM` 的 load/store、Tree language 没有 procedure definitions、`Tr_exp` 的 `Ex/Nx/Cx` 表示、patch list 和 `doPatch/joinPatch`、`unEx/unNx/unCx`、`Tr_simpleVar` 与 `F_Exp`、沿 static link 访问外层变量、Tiger array/record 是 pointer assignment、structured l-value 只作对比、string equality 调 runtime、string literal fragment、record allocation、`F_externalCall`、while/for/function call/declaration、`ProcFrag/StringFrag` 和 `procEntryExit`。
- `10_IR_Tree_中间代码生成.md` 已按教材/PPT顺序补强本章边界、IR 分类和三地址码对照、Tree IR 节点语义、`NAME`/`LABEL`、`ESEQ` 和 side effect、Ex/Nx/Cx 形态转换、patch list/backpatching、`F_Exp` 与 static link 变量访问、l-value/r-value、Tiger array/record pointer model、算术/比较/string equality、for 循环 `maxint` 细节、record/array/string/runtime call、declaration 翻译、function declaration 1-11 步、fragment 和 PPT 覆盖核对。

## 第 11 章补强依据

- 本地 `materials/ch8  (处理IR) 基本块和traces.pdf` 共 77 页，PPT 主线包括：IR Tree 到机器码的三个 mismatch，三阶段 `Linearize -> Basic Blocks -> Trace Schedule`，canonical form 定义，ESEQ 重写规则，commutativity 保守判断，CALL 提到顶层，线性语句列表，basic block 定义和构造修补，CFG 视角，trace covering 贪心算法，`CJUMP` 后续三种 finishing up 情况，删除跳到下一条 label 的冗余 `JUMP`，以及 optimal traces 只作了解。
- 虎书 Basic Blocks and Traces 章节对应内容包括：`Canon` 模块的 `C_linearize/C_basicBlocks/C_traceSchedule`，Figure 8.1 的 ESEQ rewrite identities，`reorder/do_exp/do_stm` 从表达式列表拉出 statement，`MOVE` 左侧作为 destination 的特殊处理，CALL 只允许在 `EXP(CALL(...))` 或 `MOVE(TEMP t, CALL(...))` 下，`done` label 表示函数 epilogue 入口，Algorithm 8.3 生成 traces，以及 trace 后对 `CJUMP` 的 false fall-through 修补。
- `11_规范化_基本块_Trace.md` 已按教材/PPT顺序补强本章边界、三个 mismatch、canonical tree 定义、ESEQ 改写、commute、`reorder/do_exp/do_stm`、`MOVE` 左侧 destination 特例、CALL 顶层化、linearize、basic block 构造、`done` label、CFG 后继、trace covering、longest trace 手算、`CJUMP` 三种修补、冗余 jump 删除和 PPT 覆盖核对。

## 第 12 章补强依据

- 本地 `materials/ch9 指令选择.pdf` 共 82 页，PPT 主线包括：后端三任务 instruction selection/register allocation/instruction scheduling，指令选择把 canonical IR 映射到 abstract assembly，tree pattern/tile/tiling，Jouette 指令集示例，`TEMP` tile 零成本，`a[i] := x` 多种 tiling 和 instruction emission，small tiles 保证覆盖，instruction cost 的理想化，optimal vs optimum tiling，Maximal Munch 贪心顶向下，Dynamic Programming 自底向上求最低成本，tree grammar/regular tree grammar/生成器，RISC vs CISC 差异，以及 CISC 的 register classes、two-address instructions、memory operands、addressing modes、side-effect instructions。
- 虎书 Instruction Selection 章节对应内容包括：machine instruction 作为 IR tree fragment，Figure 9.1 Jouette patterns，Figure 9.2 `a[i] := x` 两种 tiling，Maximal Munch always finds an optimal tiling but not necessarily optimum，DP cost at each node and emission on tile leaves，tree grammar 用非终结符表示寄存器类/存储位置，BURG/Twig 等工具，`AS_instr` 的 `OPER/LABEL/MOVE` 抽象汇编表示，`dst/src/jumps`，`munchExp/munchStm/munchArgs`，procedure call 的 sources/calldefs，以及 frame pointer elimination 的背景。
- `12_指令选择_Tiling.md` 已按教材/PPT顺序补强本章边界、后端三任务、instruction selection 判断题陷阱、tree pattern/tile/tiling、Jouette 和 `TEMP` 零成本、`a[i] := x` tiling 主线、small tiles、optimal vs optimum、Maximal Munch 性质、DP 成本和 tile leaves、tree grammar、RISC/CISC 对比、抽象汇编 `OPER/LABEL/MOVE`、`dst/src/jumps`、CALL clobber 建模和 PPT 覆盖核对。

## 第 13 章补强依据

- 本地 `materials/ch10 活跃变量分析.pdf` 共 88 页，PPT 主线包括：优化粒度 local/intraprocedural/interprocedural，dataflow analysis 的事实收集与转换，CFG 的 statement node 和 basic-block node 两种粒度，live variable 定义，不可判定与保守近似，forward/backward、must/may 分类，register allocation 动机，`pred/succ`、`use/def`、live-in/live-out，三条 liveness 规则，数据流方程，固定点迭代，逆控制流顺序加速，basic-block based CFG 的 `useB/defB` 扫描，set 表示，one-variable-at-a-time，复杂度、least fixed point，以及 static vs dynamic liveness。
- 虎书 Liveness Analysis 章节对应内容包括：无限 temporaries 到有限寄存器的动机，Graph 10.1/10.2 的 live range 示例，Equations 10.3 和 Algorithm 10.4，正向/反向迭代顺序对收敛速度的影响，基本块级分析、集合表示、one-variable-at-a-time，保守近似与不可判定，interference matrix/graph，move instruction 特殊处理，Tiger 编译器中从 Assem flow graph 到 liveness/interference graph 的 `FG_def/FG_use/FG_isMove`、`Live_graph`、`liveMap` 和 zero-length live ranges。
- `13_活跃变量分析.md` 已按教材/PPT顺序补强本章边界、dataflow analysis 总览、CFG 粒度、live variable 定义、static/dynamic 和保守近似、backward/may 分类、`pred/succ` 易错方向、`use/def`、abstract assembly 到 flow graph、三条 liveness 规则、`in/out` 方程、固定点迭代、反向顺序加速、block-level `useB/defB`、集合表示、顺序/分支/循环例题、interference graph、move 特殊处理、zero-length live range、Tiger 两阶段和 PPT 覆盖核对。

## 第 14 章补强依据

- 本地 `materials/ch11 寄存器分配1.pdf` 共 86 页，PPT 主线包括：register allocation 问题定义、K-coloring、干涉图、图着色复杂度、Kempe theorem、simplify/select、基础算法失败情形、optimistic coloring、potential spill 与 actual spill 的区别、spill rewrite、重新 liveness/regalloc，以及 K=4 simplify/select 示例。
- 本地 `materials/ch11 寄存器分配2.pdf` 共 73 页，PPT 主线包括：move 指令特殊建边、coalescing、Briggs criterion、George criterion、optimized algorithm with move coalescing、freeze、constrained move、precolored nodes、precolored coalescing、caller-save/callee-save 建模、spill priority 公式和 K=3 综合例子。
- 虎书 Register Allocation 章节对应内容包括：图着色寄存器分配、低度节点 simplify、select stack、spill cost、actual spill 后插入 load/store 并重建程序、move coalescing、Briggs/George conservative coalescing、precolored nodes、调用约定寄存器建模和迭代式分配流程。
- `14_寄存器分配.md` 已按教材/PPT顺序补强本章边界、interference graph 建图、move 特殊规则、K-coloring、Kempe theorem、simplify/select、optimistic coloring、potential/actual spill、spill priority、Briggs/George、constrained move、iterated register coalescing、freeze、precolored nodes、caller-save/callee-save、大题模板和判断题高频点。

## 第 15 章补强依据

- 本地 `materials/ch1 简介.pdf` 共 56 页，PPT 主线中“编译器的阶段”和“TIGER 编译器流程”覆盖：编译器定义、广义/狭义目标语言、预处理器/编译器/汇编器/链接器、JIT/AOT、前端/中端/后端、词法/语法/语义/IR/优化/目标代码生成，以及 Tiger 的 AST、IRTree、Canonicalized IRTree、Assem、CFG、InterferenceGraph 串联。
- 虎书 Introduction 的 Figure 1.1 和 Table 1.2 覆盖完整 compiler phases and interfaces：Source Program、Tokens、Abstract Syntax、Frame、IR Trees、Assem、Flow Graph、Interference Graph、Register Assignment、Code Emission，并强调每个阶段通过数据结构或抽象接口模块化连接。
- `15_完整编译器串联.md` 已按教材/PPT顺序补强本章边界、总流水线、每阶段输入输出、front/middle/back end、Token-AST、semantic environment、Frame/Level/Access、fragments、canonical tree、abstract assembly、liveness/regalloc 闭环、`procEntryExit`、code emission、runtime library、debug 定位表和小程序串联答题模板。

## 第 16 章补强依据

- 本地 `materials/ch13 垃圾回收-1.pdf` 共 87 页，PPT 主线包括：GC 技术总览、directed graph/root/reachability、freelist、mark-and-sweep、mark DFS、mark-sweep 成本、explicit stack、pointer reversal、memory fragmentation、reference counting、引用计数赋值维护、reference cycle、reference counting 优缺点。
- 本地 `materials/ch13 垃圾回收-2.pdf` 共 105 页，PPT 主线包括：copying collection、from-space/to-space、fast allocation、Cheney algorithm、pointer forwarding、BFS queue 的 scan/next、不复制死对象、locality、copying collection 优缺点、compiler interface、fast allocation 优化、pointer map/stack map、type descriptor、derived pointers，以及 pointer/non-pointer 信息贯穿 type checking、temp、spill slot、register allocation 和 code emission。
- 虎书 Garbage Collection 章节对应内容包括：garbage 的 reachability 近似、mark-and-sweep 算法、reference counts 和循环垃圾、copying collection/forwarding/Cheney、generational/incremental 概念、interface to the compiler；本课件明确 generational/incremental 书上有但不考算法细节。
- `16_垃圾回收.md` 已按 PPT/教材顺序补强本章边界、roots/reachability、freelist、mark-and-sweep、成本公式、explicit stack/pointer reversal、fragmentation、reference counting、copying collection、forwarding pointer、Cheney 手算、compiler interface、pointer map/type descriptor、safe point、derived pointer、弱化内容速记和判断/选择题高频点。
