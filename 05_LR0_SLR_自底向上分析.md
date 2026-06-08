# 05 LR(0) 与 SLR 自底向上分析

## 本章解决什么问题

自底向上分析从输入串出发，把它逐步归约成开始符号。LR 系列分析器的执行模型基本相同：维护状态栈，查 `ACTION/GOTO` 表，执行 shift、reduce、accept 或 error。

LR 的含义：

- `L`：从左到右扫描输入。
- `R`：构造最右推导的逆过程。

## Shift-Reduce 思想

分析器反复做两类动作：

- Shift：把下一个输入 token 移入栈。
- Reduce：把栈顶一段符号按某个产生式右部归约成左部非终结符。

例：

```text
E -> E + T | T
T -> id
```

输入 `id + id`：

```text
shift id
reduce T -> id
reduce E -> T
shift +
shift id
reduce T -> id
reduce E -> E + T
accept
```

## LR(0) Item

LR item 在产生式右部加一个点，表示识别进度。

```text
E -> E . + T
```

含义：已经识别出 `E`，接下来期待 `+ T`。

```text
T -> id .
```

含义：已经识别完整个右部，可以考虑按 `T -> id` 归约。

## Closure 与 Goto

### Closure

如果项集中有：

```text
A -> alpha . B beta
```

点后面是非终结符 `B`，那么要把 `B` 的所有产生式以点在最前的形式加入：

```text
B -> . gamma
```

直觉：既然接下来可能要识别 `B`，就要准备识别 `B` 的所有可能形式。

### Goto

`goto(I, X)` 表示在项集 `I` 中让点越过符号 `X` 后，再取 closure。

```text
A -> alpha . X beta
```

读入/识别 `X` 后变成：

```text
A -> alpha X . beta
```

## 构造 LR(0) 项集族

算法：

```text
augment grammar with S' -> S EOF
I0 = closure({ S' -> . S EOF })
repeat:
  for each item set I:
    for each grammar symbol X:
      J = goto(I, X)
      if J is nonempty and new:
        add J
```

每个项集是 DFA 的一个状态，边由 `goto` 给出。

## LR 手算标准流程

LR 题最容易因为漏项而错。建议按这个表格流程写：

```text
1. 增广文法：S' -> S EOF
2. 写 I0 = closure(S' -> . S EOF)
3. 对 I0 中点后面的每个符号 X 计算 goto(I0, X)
4. 新得到的项集编号为 I1, I2, ...
5. 对每个新项集重复第 3 步
6. 没有新项集时停止
7. 画 DFA：Ii --X--> Ij
8. 填 ACTION/GOTO 表
9. 用状态栈模拟输入串
```

手算 `closure` 时只看“点后面”的符号：

```text
A -> alpha . B beta
```

只有点后是非终结符 `B`，才加入 `B -> . gamma`。如果点后是终结符或点在末尾，不展开。

手算 `goto(I, X)` 时分两步：

```text
先移动点：A -> alpha . X beta 变成 A -> alpha X . beta
再对移动后的项集做 closure
```

## 从 LR(0) DFA 到 ACTION/GOTO 表

如果状态 `i` 有边：

```text
i -- terminal a --> j
```

则：

```text
ACTION[i,a] = shift j
```

如果状态 `i` 有完整项：

```text
A -> alpha .
```

则 LR(0) 会在所有终结符上填：

```text
ACTION[i,a] = reduce A -> alpha
```

如果是：

```text
S' -> S . EOF
```

则读到 EOF 后 accept。

非终结符边填 `GOTO` 表：

```text
i -- nonterminal A --> j
GOTO[i,A] = j
```

## LR 分析执行

状态栈初始为 `0`。动作：

- `shift j`：读入当前 token，把 token 和状态 `j` 入栈。
- `reduce A -> beta`：弹出 `|beta|` 个语法符号及其状态，再根据当前栈顶状态 `s` 查 `GOTO[s,A]` 入栈。
- `accept`：成功。
- `error`：语法错误。

状态栈模拟表通常写成：

| 步骤 | 状态栈 | 符号栈 | 剩余输入 | 动作 |
|---|---|---|---|---|
| 0 | `0` | empty | `id + id EOF` | 查 `ACTION[0,id]` |

每次 reduce 后要特别小心：先弹出右部长度对应的状态，再用“弹出后的栈顶状态”和产生式左部查 `GOTO`。很多错误都出在 reduce 后还用旧栈顶。

## SLR(1)

LR(0) 的问题是归约太粗：只要状态里有完整项，就对所有 lookahead 归约。SLR 改进为：

如果状态 `i` 有：

```text
A -> alpha .
```

只在 `a in FOLLOW(A)` 时填：

```text
ACTION[i,a] = reduce A -> alpha
```

SLR 仍使用 LR(0) 项集 DFA，只在填表时使用 FOLLOW 集限制归约。

## 冲突

| 冲突 | 含义 |
|---|---|
| shift/reduce conflict | 同一格既能 shift 又能 reduce |
| reduce/reduce conflict | 同一格可按多个产生式 reduce |

LR(0) 冲突不一定说明语言有问题，可能只是 LR(0) 信息不够。SLR、LR(1)、LALR 会逐步增加精度。

## 例题：完整 LR(0) 项集族与表

文法：

```text
0. S' -> S EOF
1. S  -> E
2. E  -> E + T
3. E  -> T
4. T  -> id
```

### 项集族

`I0 = closure(S' -> . S EOF)`：

```text
S' -> . S EOF
S  -> . E
E  -> . E + T
E  -> . T
T  -> . id
```

从 `I0` 出发：

```text
goto(I0, S) = I1:
S' -> S . EOF

goto(I0, E) = I2:
S  -> E .
E  -> E . + T

goto(I0, T) = I3:
E  -> T .

goto(I0, id) = I4:
T  -> id .
```

继续：

```text
goto(I1, EOF) = I5:
S' -> S EOF .

goto(I2, +) = I6:
E -> E + . T
T -> . id

goto(I6, T) = I7:
E -> E + T .

goto(I6, id) = I4
```

没有新状态后停止。DFA 边：

```text
I0 --S--> I1
I0 --E--> I2
I0 --T--> I3
I0 --id--> I4
I1 --EOF--> I5
I2 --+--> I6
I6 --T--> I7
I6 --id--> I4
```

### SLR ACTION/GOTO 表

FOLLOW 集：

```text
FOLLOW(S) = { EOF }
FOLLOW(E) = { +, EOF }
FOLLOW(T) = { +, EOF }
```

用 SLR 规则填表：

| 状态 | `id` | `+` | `EOF` | GOTO `S` | GOTO `E` | GOTO `T` |
|---|---|---|---|---|---|---|
| I0 | s4 |  |  | I1 | I2 | I3 |
| I1 |  |  | s5 |  |  |  |
| I2 |  | s6 | r1 `S->E` |  |  |  |
| I3 |  | r3 `E->T` | r3 `E->T` |  |  |  |
| I4 |  | r4 `T->id` | r4 `T->id` |  |  |  |
| I5 |  |  | accept |  |  |  |
| I6 | s4 |  |  |  |  | I7 |
| I7 |  | r2 `E->E+T` | r2 `E->E+T` |  |  |  |

`I2` 同时有完整项 `S -> E .` 和 shift 边 `+`。如果用 LR(0)，`S -> E` 会在所有终结符上归约，于是 `+` 格子出现 shift/reduce conflict；SLR 用 `FOLLOW(S)={EOF}` 限制 `S->E` 只在 EOF 上归约，因此消除这个冲突。

### 状态栈分析 `id + id EOF`

| 步骤 | 状态栈 | 符号栈 | 输入 | 动作 |
|---|---|---|---|---|
| 0 | `0` | empty | `id + id EOF` | s4 |
| 1 | `0 4` | `id` | `+ id EOF` | r4 `T->id` |
| 2 | `0 3` | `T` | `+ id EOF` | r3 `E->T` |
| 3 | `0 2` | `E` | `+ id EOF` | s6 |
| 4 | `0 2 6` | `E +` | `id EOF` | s4 |
| 5 | `0 2 6 4` | `E + id` | `EOF` | r4 `T->id` |
| 6 | `0 2 6 7` | `E + T` | `EOF` | r2 `E->E+T` |
| 7 | `0 2` | `E` | `EOF` | r1 `S->E` |
| 8 | `0 1` | `S` | `EOF` | s5 |
| 9 | `0 1 5` | `S EOF` | empty | accept |

这里状态号用 `I0=0` 等简写。实际考试只要表和栈动作一致，状态编号可以不同。

## 常见误区

- LR(0) item 里的 `0` 表示 item 没有 lookahead，不是分析器不看输入。
- Closure 是“点后非终结符”触发，不是所有非终结符都加入。
- `goto` 可以对终结符或非终结符计算；终结符边用于 ACTION，非终结符边用于 GOTO 表。
- SLR 的 DFA 与 LR(0) 相同，差别在 reduce 填表条件。
- FOLLOW 是全局近似，所以 SLR 有时仍冲突。

## 练习

1. 对文法构造 LR(0) 项集族：

```text
S -> E
E -> E + T | T
T -> id
```

2. 根据项集族填写 ACTION/GOTO 表。
3. 用表分析输入 `id + id EOF`。
4. 找一个含 shift/reduce conflict 的状态，并说明 SLR 是否能用 FOLLOW 消除它。

## 练习参考答案

见 [23_练习参考答案.md](23_练习参考答案.md) 中对应章节。

## 术语中英对照

| English | 中文 | 考试提示 |
|---|---|---|
| bottom-up parsing | 自底向上分析 | 从输入归约到开始符号 |
| shift-reduce parsing | 移进-归约分析 | LR 的执行模式 |
| shift | 移进 | 读入 token 并压状态 |
| reduce | 归约 | 右部替换为左部 |
| LR item | LR 项 | 带点产生式 |
| dot | 点 | 表示识别进度 |
| closure | 闭包 | 点后非终结符展开 |
| goto | 转移函数 | 点越过一个符号 |
| item set | 项集 | LR DFA 的状态 |
| canonical collection | 规范项集族 | 所有 LR 项集 |
| ACTION table | ACTION 表 | 终结符上的动作 |
| GOTO table | GOTO 表 | 非终结符上的状态转移 |
| shift/reduce conflict | 移进/归约冲突 | 同格两种动作 |
| reduce/reduce conflict | 归约/归约冲突 | 同格多个归约 |
| SLR parsing | SLR 分析 | FOLLOW 限制 LR(0) 归约 |
| augmented grammar | 增广文法 | 加 `S' -> S EOF` |
| handle | 句柄 | 下一步应归约的右部实例 |
| viable prefix | 可行前缀 | 可能出现在 LR 栈上的前缀 |
| LR automaton | LR 自动机 | 项集 DFA |
| parser state | 分析器状态 | 项集编号 |
| state stack | 状态栈 | LR parser 核心栈 |
| symbol stack | 符号栈 | 记录已识别符号 |
| accepting state | 接受状态 | 可执行 accept |
