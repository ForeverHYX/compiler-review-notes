# 12 指令选择与 Tiling

## 本章只学到哪里

这一章从上一章整理好的 canonical IR 出发，把 Tree IR 变成 abstract assembly code。

考试重点是：

1. 知道 instruction selection 不是“每个 IR 节点选一条指令”，而是用机器指令对应的 tree patterns 覆盖 IR tree。
2. 会区分 tile、tiling、optimal tiling、optimum tiling。
3. 会用 Maximal Munch 贪心覆盖一棵 IR tree，并知道它 always finds optimal tiling，但不保证 optimum。
4. 会用 dynamic programming 对每个节点算最低成本。
5. 知道 abstract assembly 的 `OPER/LABEL/MOVE`、`dst/src/jumps` 是后面 flow graph 和 liveness 的输入。
6. 知道 RISC/CISC 对 tile 大小、寄存器类、寻址模式的影响，但不用写真实 x86 后端。

## 本章解决什么问题

编译后端常分成三件事：

| 任务 | 本课程处理 | 作用 |
|---|---|---|
| instruction selection | 本章 | 把 canonical IR 映射到 abstract assembly |
| register allocation | 后面第 14 章 | 决定 temporaries 放在哪些物理寄存器或栈槽 |
| instruction scheduling | 本课基本不讲 | 重排指令隐藏延迟、利用流水线 |

此时还没有寄存器分配，所以输出不是最终机器汇编，而是带无限 temporaries 的 abstract assembly。

```text
canonical Tree IR
  -> instruction selection
  -> abstract assembly with temporaries
  -> register allocation
  -> real assembly registers
```

## 指令选择的核心问题

IR Tree 每个节点只表达一个原始操作，例如：

- `MEM`：读内存。
- `BINOP(PLUS,...)`：加法。
- `MOVE`：赋值/存储。

但真实机器的一条指令往往能同时做几件事。例如：

```text
MEM(BINOP(PLUS, TEMP fp, CONST k))
```

可以直接对应一条带偏移寻址的 load：

```text
LOAD r <- M[fp + k]
```

所以 instruction selection 的准确说法是：

> 找到一组目标机器指令来实现给定 IR tree。

不是：

> 给每一个 IR tree node 单独找一条机器指令。

后者是常见判断题陷阱，因为一个 tile 可能覆盖多个 IR 节点，`TEMP` tile 甚至不生成任何指令。

## Tree Pattern、Tile 和 Tiling

tree pattern 是目标机器指令对应的一小片 IR tree。

tile 就是 tree pattern 的另一种叫法。tiling 就是用这些 tiles 覆盖整棵 IR tree。

合法 tiling 要满足：

1. 每个 IR 节点都被覆盖。
2. tiles 之间不能重叠。
3. tile 的边界通过 temporary/register 连接。
4. 每个 tile 对应一条合法机器指令，除了 `TEMP` tile 这种零指令 tile。

例子：

```text
MEM(BINOP(PLUS, TEMP fp, CONST -8))
```

如果目标机器支持 `base + offset` 寻址，可以用一个大 tile 覆盖：

```text
LOAD r <- M[fp - 8]
```

如果没有这种寻址，就要用小 tile：

```text
t <- fp + -8
r <- M[t]
```

所以指令选择强依赖目标机器。

## Jouette 指令集只需要掌握什么

PPT 和虎书用 Jouette 架构讲 tiling。它是一个教学用 RISC-like 机器，考试不要求背完整指令表，但要知道这些特点：

| 特点 | 复习意义 |
|---|---|
| `r0` 恒为 0 | `CONST c` 可用 `ADDI r <- r0 + c` 生成 |
| load/store 架构 | 内存访问主要靠 `LOAD/STORE/MOVEM` |
| 寄存器较多且通用 | 比 CISC 更适合简单 tile |
| 每条普通指令成本近似 1 | 方便讲 tiling 成本 |
| `TEMP` 节点表示已有寄存器值 | `TEMP` tile 成本为 0，不发指令 |

常见 tree patterns：

| IR pattern | 指令直觉 |
|---|---|
| `TEMP t` | 已经在某个 temporary 中，无需发指令 |
| `CONST c` | `ADDI r <- r0 + c` |
| `BINOP(PLUS,e1,e2)` | `ADD r <- r1 + r2` |
| `BINOP(PLUS,e,CONST c)` | `ADDI r <- r1 + c` |
| `MEM(BINOP(PLUS,e,CONST c))` | `LOAD r <- M[r1 + c]` |
| `MOVE(MEM(addr), value)` | `STORE M[addr] <- value` |
| `MOVE(MEM(e1), MEM(e2))` | `MOVEM M[e1] <- M[e2]` |

`TEMP` tile 是零成本这一点很重要：它只是引用已有 temporary/register，不是再生成一条 mov 指令。

## 例题主线：`a[i] := x`

PPT 的大例子是：

```text
a[i] := x
```

假设：

- `i` 已在寄存器里。
- `a` 和 `x` 是 frame-resident 变量。
- `a` 的栈帧位置里存的是 array base address。
- 每个元素大小为 4。

IR 直觉：

```text
M[M[fp + a] + i * 4] := M[fp + x]
```

一种 tiling 会生成：

```text
LOAD r1 <- M[fp + a]      // 取数组基址
ADDI r2 <- r0 + 4         // 常量 4
MUL  r2 <- ri * r2        // i * 4
ADD  r1 <- r1 + r2        // 元素地址
LOAD r2 <- M[fp + x]      // 取 x 的值
STORE M[r1 + 0] <- r2     // 写入 a[i]
```

这说明：

- 一个 tile 可以覆盖多个 IR 节点。
- tile 边界需要新 temporary 保存中间结果。
- 不同 tiling 可能都合法，但成本不同。

## Small Tiles 为什么必要

只设计大 tile 可能导致某些树没法覆盖。

因此一个合理的指令模式集合通常要包含足够小的 tiles，例如：

- 单独覆盖 `CONST`。
- 单独覆盖 `MEM(e)`。
- 单独覆盖普通 `BINOP`。

这样即使没有复杂寻址模式，也能保证每棵 IR tree 都能被 tiled。

## Optimal vs Optimum Tiling

这两个词容易混，PPT 和虎书区分得很清楚。

| 概念 | 中文 | 含义 |
|---|---|---|
| optimum tiling | 全局最优覆盖 | 所有 tile 总成本最低 |
| optimal tiling | 局部最优覆盖 | 不存在两个相邻 tile 能合并成更低成本的一个 tile |

关系：

```text
Every optimum tiling is optimal.
Not every optimal tiling is optimum.
```

也就是说：

- optimum 一定 optimal。
- optimal 不一定 optimum。

为什么会不一样？因为 instruction cost 是理想化模型。大 tile 通常指令少，但不一定总成本低。PPT 里 `MOVEM` 的成本若为 `m`，不同 tiling 是否更好取决于 `m`。

现实里成本还受这些因素影响：

- pipeline。
- register allocation。
- cache。
- instruction scheduling。
- 指令长度。

考试按 PPT 的理想成本模型算即可。

## Maximal Munch

### 基本思想

Maximal Munch 是 top-down greedy tiling：

1. 从当前树根开始。
2. 找能匹配当前根的最大 tile。
3. 用这个 tile 覆盖根和附近节点。
4. 对 tile 留下的 uncovered subtrees 递归。
5. 发码时先处理 leaf subtrees，再发当前 tile 的指令。

“最大 tile”通常指覆盖节点数最多的 tile；同样大小时可任意选，或者按成本选。

### Maximal Munch 的性质

PPT 的关键结论：

```text
Maximal Munch finds an optimal tiling.
Maximal Munch does not necessarily find an optimum tiling.
```

所以判断题：

> Maximum munch always produce optimal tiling.

按本章定义应判对；但如果题目说 “always produce optimum tiling / lowest-cost tiling”，那就是错。

### 为什么不是全局最优

Maximal Munch 只看当前根部最大 tile，不回头比较全局成本。局部选择可能让子树剩下更贵的覆盖。

因此：

- 简单、快。
- 对 RISC 机器常常足够。
- 对 CISC 或复杂成本模型不保证最低成本。

### Maximal Munch 发码顺序

虽然 tiling 从根开始选 tile，但指令必须等操作数先算出来。

因此发码是：

```text
for each uncovered leaf subtree of selected tile:
  emit code for that subtree
emit instruction for selected tile
```

这可以理解为“按 tile 后序发码”，不是简单按 IR 节点后序。

### munchExp / munchStm / munchArgs

手写后端常用递归函数：

| 函数 | 作用 |
|---|---|
| `munchExp(e)` | 生成计算表达式 `e` 的指令，并返回保存结果的 temporary |
| `munchStm(s)` | 生成语句 `s` 的指令，没有返回值 |
| `munchArgs(args)` | 计算实参并放到参数寄存器或 outgoing 参数区 |

示例：

```text
munchExp(MEM(BINOP(PLUS, e, CONST k))):
  r1 = munchExp(e)
  r  = newtemp()
  emit(LOAD r <- M[r1 + k], dst={r}, src={r1})
  return r
```

注意这里的大 tile 覆盖 `MEM + PLUS + CONST`，所以 `CONST k` 不会再单独发一条 `ADDI`。

## Dynamic Programming Tiling

### 基本思想

Dynamic Programming 是 bottom-up：

1. 后序处理每个 IR node。
2. 对当前 node，枚举所有能匹配的 tile。
3. 计算：

```text
total_cost = tile_cost + sum(best_cost(tile leaves))
```

4. 选 total cost 最小的 tile，记录在当前 node。
5. 根节点的 cost 就是整棵树的 optimum cost。
6. 最后从根按记录的 tile 发码。

DP 求的是 optimum tiling，也就是全局最低成本覆盖。

### tile leaves 是什么

DP 计算成本时，不是把 tile 内部所有孩子都加进去，而是只加 tile 没覆盖的 leaf subtrees。

例如 tile：

```text
MEM(BINOP(PLUS, e, CONST k))
```

覆盖了 `MEM`、`PLUS`、`CONST k`，只留下 `e` 作为 leaf subtree。

所以成本是：

```text
LOAD tile cost + best_cost(e)
```

而不是：

```text
LOAD tile cost + cost(PLUS) + cost(CONST)
```

这是 DP 手算题最容易算错的地方。

### DP 小例子

IR：

```text
MEM(BINOP(PLUS, CONST 1, CONST 2))
```

假设：

| Tile | 成本 | 叶子 |
|---|---:|---|
| `CONST c` -> `ADDI r <- r0 + c` | 1 | 无 |
| `BINOP(PLUS,e1,e2)` -> `ADD` | 1 | `e1,e2` |
| `BINOP(PLUS,e,CONST c)` -> `ADDI` | 1 | `e` |
| `MEM(e)` -> `LOAD` | 1 | `e` |
| `MEM(BINOP(PLUS,e,CONST c))` -> `LOAD offset` | 1 | `e` |

后序算：

```text
CONST 1: cost = 1
CONST 2: cost = 1
PLUS:
  ADD(CONST1, CONST2): 1 + 1 + 1 = 3
  ADDI(CONST1, 2):     1 + 1 = 2
  ADDI(CONST2, 1):     1 + 1 = 2
  best = 2
MEM:
  LOAD(PLUS):              1 + 2 = 3
  LOAD offset(CONST1, 2):  1 + 1 = 2
  LOAD offset(CONST2, 1):  1 + 1 = 2
  best = 2
```

一种发码：

```text
ADDI r1 <- r0 + 1
LOAD r2 <- M[r1 + 2]
```

没有给 `PLUS` 单独发 `ADD/ADDI`，因为根节点选的大 tile 已经覆盖了 `PLUS`。

## Tree Grammar

对于复杂机器，手写大量 tree patterns 会很麻烦，原因包括：

- 多种寄存器类别。
- 多种 addressing modes。
- 同一个 IR 形状可用多种指令实现。
- 成本模型需要系统比较。

tree grammar 用类似文法的规则描述 tiles，把 instruction selection 变成“树上的 parsing”问题。

一条规则包含：

1. tree grammar production。
2. cost。
3. code generation template。

例如：

```text
reg  -> TEMP
reg  -> CONST
reg  -> BINOP(PLUS, reg, reg)
addr -> BINOP(PLUS, reg, CONST)
reg  -> MEM(addr)
stm  -> MOVE(MEM(addr), reg)
```

每个 nonterminal 代表一类结果位置，比如：

- general register。
- address register。
- data register。
- memory address。
- statement。

tree grammar 通常是 ambiguous 的，因为同一个 IR tree 可以有多种指令序列。普通 LL/LR parsing 技术不适合直接用在这里；实际常用 dynamic programming 的泛化来找最低成本。

工具：

| 工具/技术 | 用途 |
|---|---|
| Twig | 基于 tree grammar 的 code-generator generator |
| BURG | bottom-up rewrite grammar 工具 |
| LLVM TableGen | 描述指令模式和生成匹配表 |

考试知道它们和 regular tree grammar / instruction selector generator 的关系即可。

## RISC vs CISC

PPT 最后一部分比较 RISC 和 CISC。复习时抓住对 instruction selection 的影响。

| 方面 | RISC | CISC |
|---|---|---|
| 寄存器 | 多，通用 | 少，可能分不同类 |
| 内存访问 | load/store，算术通常只操作寄存器 | 算术可能直接访问内存 |
| 指令形式 | 常见三地址 `r1 <- r2 op r3` | 常见二地址 `r1 <- r1 op r2` |
| 指令长度 | 较规则 | 可变长 |
| tile | 小而均匀 | 大且复杂 |
| Maximal Munch | 通常足够 | 更可能和 optimum 有差距 |

### CISC 问题 1：寄存器少

解决思路：仍然生成 temporaries，让后续 register allocator 决定哪些 spill 到内存。

### CISC 问题 2：寄存器类

有些指令要求特定寄存器。例如乘法可能要求左操作数在 `eax`，高位结果写到 `edx`。

做法是显式 move：

```text
mov eax, t2
mul t3
mov t1, eax
```

再依赖寄存器分配阶段尽量 coalesce move。

### CISC 问题 3：二地址指令

二地址指令形如：

```text
r1 <- r1 + r2
```

要实现三地址 IR：

```text
t1 <- t2 + t3
```

可先生成：

```text
mov t1, t2
add t1, t3
```

如果后面寄存器分配把 `t1` 和 `t2` 放到同一物理寄存器，`mov` 可以删掉。

### CISC 问题 4：memory operands 和 addressing modes

CISC 可以有：

```text
add eax, [ebx + 8]
mov eax, [ebx + 4*ecx + 8]
```

好处：

- 更少显式临时寄存器。
- 指令编码可能更短。

但不一定更快；复杂寻址模式可能内部也要多个步骤。考试只需知道可以用更大的 specialized tile 匹配这些常见地址计算。

### CISC 问题 5：带副作用的指令

例如 autoincrement load：

```text
r2 <- M[r1]
r1 <- r1 + 4
```

它一条指令产生两个结果，很难用普通 tree pattern 表示，因为 tree pattern 通常只有一个 root result。

三种处理：

1. 忽略这种指令。
2. 在 instruction selector 里手写特殊 idiom。
3. 改用 DAG pattern 等更复杂算法。

## Abstract Assembly

### 为什么需要抽象汇编

指令选择后还没做 register allocation，所以不能直接写死物理寄存器。虎书用 `AS_instr` 表示“还没分配寄存器的汇编”。

核心信息：

| 字段 | 含义 |
|---|---|
| `assem` | 汇编模板字符串 |
| `dst` | 这条指令定义的 temporaries |
| `src` | 这条指令使用的 temporaries |
| `jumps` | 这条指令可能跳到的 labels |

模板里常见占位符：

| 占位符 | 含义 |
|---|---|
| `` `d0`` | 第 0 个 destination temp |
| `` `s0`` | 第 0 个 source temp |
| `` `j0`` | 第 0 个 jump label |

寄存器分配完成后，打印器才用 temp-to-register mapping 把这些占位符变成真实寄存器名。

### 三类 AS_instr

| 类型 | 用途 | 特点 |
|---|---|---|
| `OPER` | 普通操作、跳转、调用 | 有 `dst/src/jumps` |
| `LABEL` | 标签伪指令 | 标记可跳转位置 |
| `MOVE` | 纯数据搬移 | 后续若 `dst` 和 `src` 同寄存器，可删除 |

`MOVE` 被单独建模，是为了寄存器分配阶段做 coalescing。

### dst/src/jumps 例子

IR：

```text
MEM(BINOP(PLUS, TEMP fp, CONST 8))
```

可生成：

```text
AS_Oper(
  "LOAD `d0 <- M[`s0+8]",
  dst={t1},
  src={fp},
  jumps={}
)
```

条件跳转要列出可能跳到的 labels。若条件跳转可能 fall-through 到下一条 label，`jumps` 列表也要把 fall-through label 放进去，方便后面构造 flow graph。

### CALL 的建模

函数调用不是普通表达式。它会：

1. 使用参数寄存器或参数栈槽。
2. 定义返回值寄存器。
3. 破坏 caller-save 寄存器。

抽象汇编里要把这些写入 `src/dst`：

```text
OPER("CALL f",
     dst={return_register, caller_save_registers...},
     src={argument_registers...},
     jumps={})
```

这样 liveness analysis 才知道跨 call 活跃的 temporary 不能随便放在会被 call clobber 的寄存器里。

`munchArgs` 的返回值通常是所有实参所在 temporaries 的列表，即使汇编字符串里没有显式写出它们，也要放在 `src` 中。

## Frame Pointer 相关补充

虎书还提到一种情况：有些机器调用约定不使用真实 frame pointer，而是用：

```text
virtual FP = SP + frame_size
```

但 Translate 阶段可能已经生成了 `FP + k` 的 IR。

codegen 在 munch 时可以识别 `FP + k`，最终改成 `SP + k + frame_size`。不过 frame size 要等 register allocation 和 spill 情况确定后才完全知道，所以真实后端常把这件事延后到 procedure entry/exit 或 finalization 里。

考试通常不深挖这个点，只要知道 instruction selection 生成的是 abstract assembly，最终 frame layout 和寄存器细节还要由后续阶段处理。

## 大题手算模板

### 模板 1：Maximal Munch

1. 从根节点开始。
2. 找所有能匹配根的 tiles。
3. 选覆盖节点最多的 tile。
4. 标出 tile 没覆盖的 leaf subtrees。
5. 对 leaf subtrees 递归。
6. 发码时先发 leaf subtrees，再发当前 tile 指令。
7. `TEMP` tile 不发指令。

### 模板 2：Dynamic Programming

1. 给每个 tile 写出 cost 和 leaves。
2. 后序遍历 IR tree。
3. 每个节点枚举所有匹配 tile。
4. 用 `tile_cost + sum(best_cost(leaves))` 算候选成本。
5. 记录最低成本和选中的 tile。
6. 从 root 按记录的 tile 发码，只递归 tile leaves。

### 模板 3：写 abstract assembly

1. 写汇编模板 `assem`。
2. 所有被定义的 temporaries 放入 `dst`。
3. 所有被读取的 temporaries 放入 `src`。
4. 跳转目标放入 `jumps`。
5. `MOVE` 只用于纯 move；普通算术和 call 用 `OPER`。
6. call 的 `dst` 要包含 return register 和 caller-save clobbers，`src` 要包含参数寄存器。

## 常见误区

- instruction selection 不是每个 IR node 对一条指令，而是 tree tiling。
- `TEMP` tile 通常成本为 0，不发机器指令。
- 大 tile 通常指令少，但不一定总成本最低。
- Maximal Munch 产生 optimal tiling，但不一定产生 optimum tiling。
- DP 算根节点成本时，只加 selected tile 的 leaves 成本，不加 tile 内部已覆盖节点成本。
- 发码顺序按 tile leaves 递归，不是简单按所有 IR 节点后序。
- register allocation 在 instruction selection 之后；abstract assembly 里仍是 temporaries。
- `MOVE` 指令单独建模是为了后面 coalescing。
- CALL 必须建模 clobber，否则 liveness 和 register allocation 会错。
- CISC 大寻址模式不一定更快，只是可能少用寄存器、编码更短。

## 本章覆盖核对

读完本章后，你应该能对照 PPT 勾掉这些点：

- 后端三任务：instruction selection、register allocation、instruction scheduling。
- instruction selection 的输入/输出：canonical IR -> abstract assembly。
- tree pattern、tile、tiling。
- Jouette 的教学意义和 `TEMP` 零成本。
- `a[i] := x` 例子的地址计算、取数组基址、取 `x`、store。
- small tiles 保证任意 IR tree 可覆盖。
- optimal vs optimum 的定义和包含关系。
- Maximal Munch 的 top-down greedy 流程和性质。
- Dynamic Programming 的 bottom-up cost 计算。
- tile leaves 在 DP 成本和发码中的作用。
- tree grammar、regular tree grammar、nonterminal、cost、template。
- Twig、BURG、LLVM TableGen 与 instruction selector generator 的关系。
- RISC vs CISC 对 tile 和寄存器/寻址模式的影响。
- CISC register classes、two-address instructions、memory operands、side-effect instructions。
- abstract assembly 的 `OPER/LABEL/MOVE`。
- `assem/dst/src/jumps` 的含义。
- `munchExp/munchStm/munchArgs` 的职责。
- CALL 的参数源、返回值和 caller-save clobber 建模。

## 练习

1. 给一棵 IR tree 和一组 tiles，画出一种合法 tiling。
2. 用 Maximal Munch 覆盖同一棵树，并写出发码顺序。
3. 给 tile 成本，用 dynamic programming 求 root 的最低成本和选中 tile。
4. 判断一个 tiling 是 optimal、optimum，还是两者都不是。
5. 对一条 abstract assembly 写出 `dst/src/jumps`。
6. 解释一个 `CALL` 指令为什么要把 caller-save registers 放进 `dst`。

## 练习参考答案

见 [23_练习参考答案.md](23_练习参考答案.md) 中对应章节。

## 术语中英对照

| English | 中文 | 考试提示 |
|---|---|---|
| instruction selection | 指令选择 | canonical IR -> abstract assembly |
| abstract assembly | 抽象汇编 | 还没分配物理寄存器 |
| tree pattern | 树模式 | 一条机器指令对应的 IR fragment |
| tile | 覆盖片 | tree pattern 的另一种叫法 |
| tiling | 树覆盖 | 用非重叠 tiles 覆盖整棵 IR tree |
| optimal tiling | 局部最优覆盖 | 相邻 tile 不能合并成更低成本 tile |
| optimum tiling | 全局最优覆盖 | 总成本最低 |
| Maximal Munch | 最大吞噬算法 | top-down greedy，optimal but not necessarily optimum |
| dynamic programming | 动态规划 | bottom-up 求 optimum |
| tile leaf | tile 叶子 | tile 未覆盖、需要递归发码的子树 |
| tree grammar | 树文法 | 用规则描述 tiles |
| regular tree grammar | 正则树文法 | instruction selector generator 常用形式 |
| nonterminal | 非终结符 | 表示 register class / addr / stmt 等类别 |
| code generation template | 代码生成模板 | 选中规则后发出的指令 |
| Twig | 指令选择生成器 | tree grammar + DP |
| BURG | bottom-up rewrite grammar | 指令选择生成器 |
| LLVM TableGen | LLVM 表描述工具 | 描述指令模式等 |
| RISC | 精简指令集 | 小 tile，load/store，寄存器较通用 |
| CISC | 复杂指令集 | 大 tile，寄存器类和寻址模式复杂 |
| addressing mode | 寻址模式 | 如 base+offset、scaled index |
| two-address instruction | 二地址指令 | 一个操作数同时是 src 和 dst |
| autoincrement | 自增寻址 | 一条指令产生两个结果，难用 tree pattern 表达 |
| OPER | 普通抽象汇编指令 | 算术、跳转、call 等 |
| LABEL | 标签伪指令 | 跳转目标 |
| MOVE | 搬移指令 | 可在寄存器分配时 coalesce |
| destination, dst | 目标 | 指令定义的 temporaries |
| source, src | 源 | 指令使用的 temporaries |
| jumps | 跳转目标列表 | flow graph 构造需要 |
| munchExp | 表达式 munch | 生成表达式指令并返回 temporary |
| munchStm | 语句 munch | 生成语句指令 |
| munchArgs | 参数 munch | 计算实参并放到调用位置 |
| clobber | 破坏寄存器 | CALL 改写 caller-save 等寄存器 |
