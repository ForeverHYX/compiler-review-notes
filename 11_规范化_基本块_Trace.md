# 11 规范化、基本块与 Trace

## 本章只学到哪里

这一章接在 IR Tree 之后，目标不是做高级优化，而是把前端生成的 Tree IR 整理成后端容易处理的形状。

考试只需要掌握三件事：

1. 把 Tree IR 规范化成没有 `ESEQ`、没有乱嵌套 `CALL`、没有嵌套 `SEQ` 的线性语句表。
2. 把线性语句表切成 basic blocks。
3. 把 basic blocks 排成 traces，并让 `CJUMP` 后面尽量跟它的 false label。

PPT 里提到的 hot path、instruction cache、optimal trace 只是说明 trace scheduling 为什么有用，不要求展开成优化算法。

## 本章解决什么问题

上一章的 Tree IR 很适合从 AST 生成，但它和真实机器代码还有三个不匹配：

| Tree IR 现象 | 机器代码问题 | 本章处理方式 |
|---|---|---|
| `CJUMP(op,a,b,t,f)` 有 true/false 两个目标 | 大多数机器条件跳转只有一个显式目标，另一个方向顺序落下 | 后面用 trace scheduling 让 false label 紧跟 `CJUMP` |
| `ESEQ(s,e)` 把 statement 藏进 expression | 子表达式求值顺序会影响副作用 | 规范化时把 `s` 拉到外层 |
| `CALL` 可以作为任意子表达式 | 所有函数返回值通常写到同一个返回寄存器，嵌套调用会覆盖；调用还可能改参数寄存器和内存 | 把 `CALL` 提到顶层，只允许特定父节点 |

因此本章主线是：

```text
Tree IR
  -> canonical trees / linear statement list
  -> basic blocks
  -> traces
  -> 更适合 instruction selection 的语句顺序
```

## 本章考试能力清单

- 判断题：能判断 “构造 canonical tree 要 eliminate all CJUMPs” 是错的。
- 判断题：能解释 `CALL` 为什么要提到顶层，以及 “Move CALL to top node” 的准确含义。
- 选择题：能分辨 `ESEQ`、`SEQ`、`CJUMP`、`CALL` 在规范化中的处理目标。
- 手算题：能把含 `ESEQ` 的表达式改写成语句序列，必要时引入临时变量。
- 手算题：能根据一串 labeled IR 或三地址代码划分 basic blocks。
- 手算题：能从 CFG/basic blocks 中给出一个 trace 或 longest trace。
- 调度题：能处理 `CJUMP` 后面跟 false label、true label、neither label 三种情况。

## 三阶段总览

虎书和 PPT 都把这一章分成三阶段：

| 阶段 | 输入 | 输出 | 核心动作 |
|---|---|---|---|
| 1. Linearize / canonical trees | Tree statement | 线性 statement list | 消除 `ESEQ`，限制 `CALL` 父节点，消除嵌套 `SEQ` |
| 2. Basic blocks | 线性 statement list | basic block 列表和 `done` label | 每块以 `LABEL` 开头，以 `JUMP/CJUMP` 结尾，中间无跳转/标签 |
| 3. Trace schedule | basic block 列表 | 重排后的 statement list | 用 traces 覆盖所有 block，修补 `CJUMP` 的 false fall-through |

注意：这三阶段都主要是“整理形状”，不是传统意义的程序优化。

## Stage 1: Canonical Trees

### Canonical Form 的精确定义

一个 Tree IR 变成 canonical form 后，应满足：

1. 没有 `ESEQ`。
2. 没有嵌套在表达式里的 `SEQ`；最后只剩线性语句表，或者等价地 `SEQ(s1, SEQ(s2, ...))`。
3. 每个 `CALL` 的父节点只能是：
   - `EXP(CALL(...))`：调用只为了副作用或返回值不用。
   - `MOVE(TEMP t, CALL(...))`：调用产生的返回值马上保存到临时变量。

不要把第 3 点误解成 “`CALL` 必须成为整棵 IR Tree 的根”。它的意思是 `CALL` 不能藏在 `BINOP`、`MEM`、另一个 `CALL` 的参数等复杂表达式里。

### 为什么要消除 ESEQ

`ESEQ(s,e)` 的语义是：

```text
先执行 statement s
再计算 expression e
整个 ESEQ 的值就是 e 的值
```

问题是，一旦 `ESEQ` 出现在表达式内部，左右子树的求值顺序就不能随便换。

例如：

```text
BINOP(PLUS,
  TEMP a,
  ESEQ(MOVE(TEMP a, CONST 5), TEMP a))
```

如果先算左边，结果里左边的 `TEMP a` 是旧值；如果先执行右边的 `MOVE`，左边再读到的是新值。指令选择阶段不应该再背这个复杂性，所以规范化要把 `ESEQ` 全部拉出来。

### ESEQ 基本改写规则

记忆时不需要背所有形式，理解“先把副作用语句拿出来，保持原求值顺序”即可。

常见规则：

| 原形式 | 改写方向 | 解释 |
|---|---|---|
| `ESEQ(s1, ESEQ(s2,e))` | `ESEQ(SEQ(s1,s2), e)` | 两段副作用按顺序合并 |
| `BINOP(op, ESEQ(s,e1), e2)` | `ESEQ(s, BINOP(op,e1,e2))` | 左操作数里的副作用本来就先发生 |
| `MEM(ESEQ(s,e))` | `ESEQ(s, MEM(e))` | 先算地址副作用，再读内存 |
| `JUMP(ESEQ(s,e))` | `SEQ(s, JUMP(e))` | 跳转目标表达式前的副作用先执行 |
| `CJUMP(op,ESEQ(s,e1),e2,t,f)` | `SEQ(s, CJUMP(op,e1,e2,t,f))` | 左比较表达式里的副作用先执行 |
| `MOVE(TEMP t,ESEQ(s,e))` | `SEQ(s, MOVE(TEMP t,e))` | 先执行 `s`，再赋值 |
| `EXP(ESEQ(s,e))` | `SEQ(s, EXP(e))` | 先执行 `s`，再求值并丢弃结果 |

### 第二个操作数里的 ESEQ 为什么麻烦

形式：

```text
BINOP(op, e1, ESEQ(s,e2))
```

直觉上想改成：

```text
ESEQ(s, BINOP(op,e1,e2))
```

但这会把 `s` 提到 `e1` 前面。如果 `s` 会修改 `e1` 读取的临时变量或内存，就改变语义。

安全但保守的改法是引入新临时变量：

```text
ESEQ(
  MOVE(TEMP t, e1),
  ESEQ(s, BINOP(op, TEMP t, e2))
)
```

意思是：先按原顺序算出 `e1` 并保存，再执行 `s`，最后计算二元运算。

`CJUMP(op, e1, ESEQ(s,e2), l1, l2)` 同理：

```text
SEQ(
  MOVE(TEMP t, e1),
  SEQ(s, CJUMP(op, TEMP t, e2, l1, l2))
)
```

### Commute

如果能证明 statement `s` 不会影响 expression `e` 的值，就说 `s` 和 `e` commute。

```text
commute(s,e) = true
```

考试中掌握 PPT 的保守判断即可：

| 情况 | 是否可认为 commute | 原因 |
|---|---|---|
| `e` 是 `CONST` | 是 | 常量不受副作用影响 |
| `e` 是 `NAME` | 是 | label 地址不受副作用影响 |
| `s` 是空语句 `EXP(CONST 0)` | 是 | 空语句没有副作用 |
| 其他情况 | 保守认为否 | 临时变量、内存、I/O 可能被影响 |

更精细的别名分析不属于本章考试重点。保守返回 false 不会错，只会多生成临时变量。

### reorder / do_exp / do_stm 在做什么

虎书实现里常见三个名字：

| 函数 | 直觉 | 你需要知道的程度 |
|---|---|---|
| `do_exp(e)` | 把表达式 `e` 规范化成 `(statement, pure expression)` | 能解释它会把 `ESEQ` 的 statement 部分拉出来 |
| `do_stm(s)` | 把语句 `s` 规范化 | 能处理 `MOVE/JUMP/CJUMP/EXP/SEQ` 等语句里的子表达式 |
| `reorder(exps)` | 对一组子表达式保持求值顺序地重排 | 能解释必要时保存左边表达式到临时变量 |

`reorder` 的返回结果可以理解为：

```text
先执行这些 statement
再使用这些不含 ESEQ 的 expression
```

特别注意 `MOVE`：

- `MOVE(TEMP a, e)` 中，`TEMP a` 是目的地，不是要先读取的子表达式；只需要规范化右侧 `e`。
- `MOVE(MEM(e1), e2)` 中，`e1` 是要计算的地址，所以 `e1` 和 `e2` 都是子表达式，要按顺序处理。
- 这也是虎书练习里常考的坑：不要把所有 `MOVE(dst, src)` 的 `dst` 都当成普通表达式。

### Move CALLs To Top Level

Tree IR 允许：

```text
BINOP(PLUS, CALL(f, []), CALL(g, []))
```

但真实机器里 `f()` 和 `g()` 的返回值通常都会放到同一个返回值寄存器 `RV`。如果先调用 `f`，再调用 `g`，`g` 会覆盖 `f` 的返回值。

规范化规则：

```text
CALL(fun,args)
  -> ESEQ(MOVE(TEMP t, CALL(fun,args)), TEMP t)
```

例如：

```text
BINOP(PLUS, CALL(f, []), CALL(g, []))
```

规范化后等价于：

```text
MOVE(TEMP t1, CALL(f, []))
MOVE(TEMP t2, CALL(g, []))
BINOP(PLUS, TEMP t1, TEMP t2)
```

最终合法的 `CALL` 只会出现在：

```text
EXP(CALL(...))
MOVE(TEMP t, CALL(...))
```

这就是考试选项里 “Moving CALL to top node” 的真正含义。

### Eliminate SEQ / Linearize

当 `ESEQ` 和非法 `CALL` 都处理完后，`SEQ` 基本只剩在 statement 顶层，用来表示顺序执行：

```text
SEQ(s1, SEQ(s2, SEQ(s3, s4)))
```

`linearize` 把它展平成 statement list：

```text
s1
s2
s3
s4
```

所以 canonicalization 可以概括为：

```text
eliminate ESEQ
move CALLs to top level
eliminate nested SEQ by linearizing
```

不能概括为：

```text
eliminate all CJUMPs
```

`CJUMP` 仍然保留，只是在后面 trace scheduling 阶段调整物理顺序和 false fall-through。

## Stage 2: Basic Blocks

### Basic Block 定义

basic block 是一段连续语句，满足：

1. 第一条语句是 `LABEL`。
2. 最后一条语句是 `JUMP` 或 `CJUMP`。
3. 中间没有 `LABEL`、`JUMP`、`CJUMP`。
4. 控制流只能从第一条进入，从最后一条离开。

它不是源语言里的 `{ ... }` block，也不是 Tiger 的 let block。

### 为什么每块必须以跳转结束

如果每个 basic block 都以显式跳转结束，那么 block 的物理排列顺序就不影响语义：

```text
Block A: ... JUMP Lc
Block B: ...
Block C: LABEL Lc ...
```

即使把 `Block C` 挪到 `Block B` 前面，只要跳转目标不变，程序控制流仍然正确。正因为这样，后面的 trace scheduling 才能重排 basic blocks。

### Basic Block 构造算法

从线性语句表从前往后扫：

1. 遇到 `LABEL`，开始一个新 block。
2. 遇到 `JUMP` 或 `CJUMP`，结束当前 block。
3. 如果当前 block 没有以 `LABEL` 开头，补一个新 label。
4. 如果遇到新 `LABEL` 时当前 block 还没结束，给当前 block 补 `JUMP` 到这个新 label。
5. 如果整个函数最后还有未结束的 block，补 `JUMP(NAME done)`。

`done` label 表示函数 epilogue 的入口。它不是为了让你多画一个普通源代码块，而是让最后一个 block 也满足“以 jump 结尾”。

伪代码：

```text
for each statement s:
  if s is LABEL:
    if current block is open and has no jump:
      append JUMP(NAME s.label)
      close current block
    start new block with s

  else:
    if no current block:
      start new block with LABEL(newLabel)
    append s
    if s is JUMP or CJUMP:
      close current block

after scan:
  if current block is open:
    append JUMP(NAME done)
```

### Basic Block 例题

线性语句：

```text
LABEL L1
MOVE(TEMP a, CONST 1)
CJUMP(LT, TEMP a, TEMP b, L2, L3)
LABEL L2
MOVE(TEMP x, CONST 2)
LABEL L3
MOVE(TEMP x, CONST 3)
```

切分：

```text
Block 1:
  LABEL L1
  MOVE(TEMP a, CONST 1)
  CJUMP(LT, TEMP a, TEMP b, L2, L3)

Block 2:
  LABEL L2
  MOVE(TEMP x, CONST 2)
  JUMP(NAME L3)      // 因为下一个 LABEL 是 L3，当前块不能直接穿过去

Block 3:
  LABEL L3
  MOVE(TEMP x, CONST 3)
  JUMP(NAME done)    // 函数体末尾补 done
```

### 从 Basic Blocks 到 CFG

在本章里，CFG 的 node 通常是 basic block：

- `JUMP(NAME L)`：边指向 label 为 `L` 的 block。
- `CJUMP(op,a,b,Lt,Lf)`：两条边分别指向 `Lt` 和 `Lf`。
- 非跳转语句没有单独控制流边，因为它们都在块内部顺序执行。

后面活跃变量分析也会讲 CFG，但那时 node 也可能是 single statement。考试时看题目上下文。

## Stage 3: Trace Scheduling

### 为什么要重排 Basic Blocks

basic blocks 已经显式跳转，所以可以安全重排。重排的主要目的：

1. 让 `CJUMP(cond, Lt, Lf)` 后面紧跟 `LABEL Lf`。
2. 让 `JUMP(NAME L)` 后面如果刚好是 `LABEL L`，就可以删除这个冗余 jump。

真实机器条件跳转通常形如：

```text
if cond jump Lt
// false branch falls through here
```

所以 Tree IR 里的 false label 最好就是下一条物理指令所在的 label。

### Trace 和 Trace Covering

trace 是一串可能在一次执行中连续走到的 basic blocks。

trace covering 是一组 traces，满足：

1. 每个 basic block 恰好属于一个 trace。
2. 一个 trace 内尽量沿着 `JUMP` 或某个 `CJUMP` 后继继续走。
3. PPT 中要求 trace loop-free；一般手算题按“已标记 block 不再加入当前 trace”即可。

注意：一个真实程序运行时可能走很多不同路径；trace covering 只是编译器选择的一种代码布局，不是唯一答案。

### 贪心 Trace 生成算法

PPT 和虎书 Algorithm 8.3 的做法：

```text
把所有 blocks 放入列表 Q
while Q 非空:
  新建一个 trace T
  从 Q 中取一个未标记 block b
  while b 未标记:
    标记 b
    把 b 加入 T
    查看 b 的后继
    如果存在未标记后继 c:
      b = c
    否则:
      结束当前 trace
```

选择哪个未标记后继，题目不指定时可以任选；如果题目问 longest trace，就优先选能继续走得最长的一条。多个最长答案时，给出一个即可。

### Trace 例题模板

假设 CFG 边为：

```text
A -> B
B -> C or D
C -> E
D -> F
E -> done
F -> done
```

一种 trace covering 可以是：

```text
Trace 1: A, B, C, E
Trace 2: D, F
```

另一种也可能合法：

```text
Trace 1: A, B, D, F
Trace 2: C, E
```

只要每个 block 恰好出现一次，并且 trace 内按 CFG 后继连接，就符合基本要求。

### Finishing Up: 修补 CJUMP

trace 排好后，要逐个检查 `CJUMP(op,a,b,Lt,Lf)` 后面紧跟的 label。

#### 情况 1：后面正好是 false label

```text
CJUMP(GT, x, y, Lt, Lf)
LABEL Lf
```

已经符合机器 fall-through 形态，保持不变。

#### 情况 2：后面正好是 true label

```text
CJUMP(GT, x, y, Lt, Lf)
LABEL Lt
```

把条件取反，并交换 true/false label：

```text
CJUMP(LE, x, y, Lf, Lt)
LABEL Lt
```

这样 false branch 就是后面的 `Lt`。

常见取反：

| 原条件 | 取反 |
|---|---|
| `EQ` | `NE` |
| `NE` | `EQ` |
| `LT` | `GE` |
| `LE` | `GT` |
| `GT` | `LE` |
| `GE` | `LT` |

#### 情况 3：后面既不是 true label，也不是 false label

```text
CJUMP(GT, x, y, Lt, Lf)
LABEL Lother
```

插入一个新的 false label：

```text
CJUMP(GT, x, y, Lt, Lf_new)
LABEL Lf_new
JUMP(NAME Lf)
LABEL Lother
```

这样 `CJUMP` 的 false fall-through 先落到 `Lf_new`，再无条件跳到原来的 false label `Lf`。

### 删除冗余 JUMP

如果出现：

```text
JUMP(NAME L)
LABEL L
```

这个 `JUMP` 可以删掉，因为顺序执行本来就会落到 `LABEL L`。

这只是简单 peephole cleanup，不是本章主线优化题。

## 大题手算模板

### 模板 1：规范化含 ESEQ 的表达式

步骤：

1. 找最内层 `ESEQ(s,e)`。
2. 判断它在左操作数、右操作数、地址、跳转目标、赋值右侧还是函数参数里。
3. 如果拉出 `s` 会越过左边表达式，检查 commute。
4. 不能证明 commute 时，引入 `TEMP t` 保存左边表达式。
5. 所有 `CALL` 改成 `MOVE(TEMP t, CALL(...))` 或 `EXP(CALL(...))`。
6. 最后把 `SEQ` 展平成线性语句表。

### 模板 2：划分 Basic Blocks

步骤：

1. 从第一条语句开始扫。
2. 每遇到 `LABEL`，考虑是否要结束前一个块并补 `JUMP`。
3. 每遇到 `JUMP/CJUMP`，当前块结束。
4. 没有开头 label 就补新 label。
5. 最后没 jump 就补 `JUMP done`。
6. 给每个 block 写出起始 label 和末尾跳转。

### 模板 3：给出 Longest Trace

步骤：

1. 先画 block-level CFG。
2. 从题目给的入口 block 开始，沿未标记后继走。
3. `JUMP` 后继唯一，必须跟。
4. `CJUMP` 有两个后继，题目不指定时选能走更长未标记链的后继。
5. 当前 block 的后继都已标记时，当前 trace 结束。
6. 如果题目要求 trace covering，再从剩余未标记 block 继续生成 traces。

## 常见误区

- canonicalization 不会删除所有 `CJUMP`；它只是为后端整理 IR。
- `CALL` 提到顶层不是说整个函数只剩 CALL，而是说 `CALL` 的父节点受限。
- `commute` 判断可以很保守，不能为了少生成临时变量而改变语义。
- `MOVE(TEMP a,e)` 的 `TEMP a` 是目的地；`MOVE(MEM(e1),e2)` 的 `e1` 才是地址表达式，需要先计算。
- basic block 是 IR/汇编层面的连续语句块，不是源代码的 block。
- trace scheduling 允许改变 block 的物理顺序，但不能改变跳转目标表达的控制流。
- `CJUMP` 后面跟 true label 时，要取反条件并交换 label；不要只交换 label 不改条件。
- 插入新的 false label 时，新 label 后面要 `JUMP` 到原来的 false label。

## 本章覆盖核对

读完本章后，你应该能对照 PPT 勾掉这些点：

- Tree IR 和机器码的三个 mismatch。
- canonical tree 的两个核心要求：无 `SEQ/ESEQ` 嵌套，`CALL` 父节点受限。
- `ESEQ` rewrite identities 的方向和临时变量引入原因。
- `commute(s,e)` 的保守判断。
- `reorder/do_exp/do_stm` 的作用。
- `MOVE` 左侧 destination 的特殊处理。
- `linearize` 把顶层 `SEQ` 展平成 statement list。
- basic block 的四条定义。
- basic block 构造中的补 label、补 jump、补 `done`。
- CFG 里 block 后继如何由 `JUMP/CJUMP` 决定。
- trace / trace covering / marked block。
- trace 生成的贪心算法。
- `CJUMP` finishing up 的三种情况。
- 删除 `JUMP(NAME L); LABEL L` 这种冗余 jump。

## 练习

1. 把含 `ESEQ` 的表达式改写成无 `ESEQ` 的语句列表，并说明何时需要新临时变量。
2. 把一串 `LABEL/JUMP/CJUMP` 语句划分为 basic blocks。
3. 给 CFG，选一组 trace covering；如果有多个答案，说明你的选择依据。
4. 对 `CJUMP` 后面分别跟 false label、true label、neither label 三种情况写出修补结果。

## 练习参考答案

见 [23_练习参考答案.md](23_练习参考答案.md) 中对应章节。

## 术语中英对照

| English | 中文 | 考试提示 |
|---|---|---|
| canonical form | 规范形式 | 适合后端处理的 IR 形状 |
| canonical tree | 规范树 | 无 `ESEQ`，`CALL` 父节点受限 |
| canonicalization | 规范化 | 消除 `ESEQ`、提 `CALL`、线性化 |
| linearize | 线性化 | 把顶层 `SEQ` 展成语句表 |
| linear statement list | 线性语句表 | 后续切 basic blocks 的输入 |
| ESEQ | expression sequence | statement 藏在 expression 里 |
| SEQ | statement sequence | 顶层顺序执行语句 |
| commute | 可交换 | `s` 不影响 `e` 的值 |
| reorder | 表达式重排 | 保持求值顺序地拉出副作用 |
| do_exp | 处理表达式 | 返回 statement 和纯 expression |
| do_stm | 处理语句 | 规范化语句内部子表达式 |
| basic block | 基本块 | 单入口、单出口、内部无标签/跳转 |
| CFG | 控制流图 | 本章 node 通常是 basic block |
| trace | 执行迹 | 可能连续执行的一串 basic blocks |
| trace covering | trace 覆盖 | 每个 block 恰好属于一个 trace |
| marked block | 已标记块 | trace 生成中已经选过的 block |
| trace scheduling | trace 调度 | 重排 basic blocks |
| fall-through | 顺序落下 | 不跳转，直接执行下一条 |
| false label | 假分支标签 | 机器条件跳转的 fall-through 方向 |
| condition negation | 条件取反 | 后面跟 true label 时使用 |
| redundant jump | 冗余跳转 | `JUMP L` 后面紧跟 `LABEL L` |
| done label | 结束标签 | 函数 epilogue 入口 |
