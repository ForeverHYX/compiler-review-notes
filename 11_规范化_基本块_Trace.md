# 11 规范化、基本块与 Trace

## 本章解决什么问题

Tree IR 容易从 AST 生成，但还不适合指令选择。规范化要把复杂树变成接近汇编的线性语句序列。

主要目标：

1. 去掉 `ESEQ`。
2. 把 `CALL` 提到合适位置，避免嵌套调用干扰参数/返回寄存器。
3. 形成线性语句。
4. 划分 basic block。
5. 重排 trace，使条件跳转更接近真实机器代码。

## 为什么要规范化

Tree IR 与机器码有几个不匹配：

- `CJUMP` 有 true/false 两个目标，但真实机器条件跳转通常一个目标，另一个 fall-through。
- `ESEQ` 把语句藏在表达式里，求值顺序复杂。
- `CALL` 会改写返回值寄存器和 caller-save 寄存器，嵌套调用危险。

## Canonical Tree

规范形式大致要求：

- 没有 `SEQ` 和 `ESEQ` 嵌在表达式中。
- 每个 `CALL` 不嵌在另一个表达式里，通常先 `MOVE(TEMP t, CALL(...))`。
- 线性语句列表中控制流显式。

## Commute

规范化时要判断语句 `s` 和表达式 `e` 能否交换顺序。

保守规则：

```text
commute(s, e) = true if s has no side effect or e is CONST/NAME
```

实际实现可以更精细，但保守正确比激进错误更重要。

## Canonicalization 重写规则

规范化核心是把“藏在表达式里的语句”提出来，同时保持求值顺序。

常见规则：

| 原形式 | 目标 |
|---|---|
| `SEQ(SEQ(a,b),c)` | 展平成 `a; b; c` |
| `ESEQ(s,e)` 出现在表达式里 | 先执行 `s`，再使用 `e` |
| `CALL` 作为子表达式 | 先 `MOVE(TEMP t, CALL(...))`，再使用 `TEMP t` |
| `MOVE(TEMP t, ESEQ(s,e))` | `s; MOVE(TEMP t,e)` |
| `EXP(ESEQ(s,e))` | `s; EXP(e)` |

如果不能证明 `s` 与后面的表达式可交换，就引入临时变量保护顺序：

```text
BINOP(PLUS, ESEQ(s, e1), e2)
```

可改成：

```text
s
t := e1
BINOP(PLUS, TEMP t, e2)
```

这样不会把 `e2` 提前到 `s` 前面。

教材实现常见函数：

```text
do_stm(s): 规范化语句
do_exp(e): 返回 (语句列表, 纯表达式)
reorder(exps): 规范化一组表达式并保持求值顺序
```

## Linearize

`linearize` 把嵌套的 `SEQ` 展平为语句列表：

```text
SEQ(s1, SEQ(s2, s3))
```

变成：

```text
s1
s2
s3
```

## Basic Block

基本块是一段连续语句：

- 第一条是 `LABEL`。
- 中间没有 `LABEL`。
- 最后一条是 `JUMP` 或 `CJUMP`。
- 只能从第一条进入，只能从最后一条离开。

如果某段没有以 `LABEL` 开头，就补一个；如果没有以 jump 结尾，就补 `JUMP` 到下一块。

### 从线性语句到 Basic Blocks

算法：

```text
blocks = []
current = []
for each statement s in linear list:
  if s is LABEL:
    if current 非空且未以 JUMP/CJUMP 结束:
      current.append(JUMP(s.label))
      blocks.add(current)
    current = [s]
  else:
    if current 为空:
      current = [LABEL(newLabel)]
    current.append(s)
    if s is JUMP or CJUMP:
      blocks.add(current)
      current = []
如果 current 非空:
  current.append(JUMP(done))
```

这保证每个块都以 label 开头、以 jump 结尾。

## Trace Scheduling

Trace 是把可能连续执行的 basic blocks 串起来。目标是减少无用跳转，并让 `CJUMP` 的 false label 紧跟在后面。

对 `CJUMP(op,a,b,t,f)`：

1. 如果下一个块就是 `f`，很好。
2. 如果下一个块是 `t`，可以反转条件，交换 `t/f`。
3. 如果都不是，插入一个新的 false label 和 jump。

### Trace 生成算法

```text
把所有 block 标记为 unmarked
while 还有 unmarked block:
  从某个 unmarked block 开始新 trace
  while 当前 block 未标记:
    标记当前 block
    加入 trace
    如果当前 block 以 JUMP 结尾且目标未标记:
      current = 目标 block
    else if 当前 block 以 CJUMP 结尾:
      优先选择一个未标记后继继续
    else:
      stop
```

最终所有 trace 覆盖每个 block 一次，这叫 `trace covering`。重排后再处理每个 trace 末尾的 `CJUMP`，尽量让 false 分支成为 fall-through。

## 例题：Basic Block 切分

线性语句：

```text
LABEL L1
MOVE(a,1)
CJUMP(<,a,b,L2,L3)
LABEL L2
MOVE(x,2)
LABEL L3
MOVE(x,3)
```

切分：

```text
Block 1:
  LABEL L1
  MOVE(a,1)
  CJUMP(<,a,b,L2,L3)

Block 2:
  LABEL L2
  MOVE(x,2)
  JUMP L3        // 因为遇到下一个 LABEL 前没有跳转，补 jump

Block 3:
  LABEL L3
  MOVE(x,3)
  JUMP done      // 结尾补 jump
```

## 例题：CJUMP 调整

原序列：

```text
CJUMP(<, a, b, Ltrue, Lfalse)
LABEL Ltrue
...
```

真实机器更希望 false fall-through。如果当前下一块是 `Ltrue`，可改为：

```text
CJUMP(>=, a, b, Lfalse, Ltrue)
LABEL Ltrue
...
```

条件反转后，false 分支就是 fall-through。

## 常见误区

- basic block 是线性语句块，不是源语言里的 `{}` block。
- trace 重排不改变程序语义，只改变块的排列和跳转形式。
- 规范化不是优化，主要是为后端降低复杂度。
- `CALL` 的问题不仅是返回值，还有参数寄存器和副作用。
- `commute` 可以保守返回 false，最多生成多一点临时变量。

## 练习

1. 把含 `ESEQ` 的表达式改写成无 `ESEQ` 的语句列表。
2. 把一串 `LABEL/JUMP/CJUMP` 语句划分为 basic blocks。
3. 给 CFG，选一组 trace 并重排。
4. 对 `CJUMP` 的三种情况分别写出处理方法。

## 练习参考答案

见 [23_练习参考答案.md](23_练习参考答案.md) 中对应章节。

## 术语中英对照

| English | 中文 | 考试提示 |
|---|---|---|
| canonical form | 规范形式 | 适合后端处理的 IR |
| canonicalization | 规范化 | 消除 ESEQ/嵌套 CALL 等 |
| reorder | 重排表达式 | 保持求值顺序 |
| do_stm | 规范化语句函数 | Appel 实现名 |
| do_exp | 规范化表达式函数 | 返回语句和纯表达式 |
| linearize | 线性化 | Tree -> 语句列表 |
| linear statement list | 线性语句表 | 无嵌套 SEQ 的语句序列 |
| basic block | 基本块 | 单入口单出口语句序列 |
| trace | 执行迹 | 可能连续执行的块序列 |
| trace covering | trace 覆盖 | 每个块属于一个 trace |
| marked block | 已标记块 | trace 生成中已选 |
| redundant jump | 冗余跳转 | 跳到下一条 label 的 jump |
| condition negation | 条件取反 | 交换 true/false label |
| trace scheduling | Trace 调度 | 重排基本块 |
| fall-through | 顺序落下 | 不跳转直接执行下一条 |
| side effect | 副作用 | 影响求值顺序 |
| commute | 可交换 | 判断语句和表达式能否换序 |
| conditional branch | 条件分支 | 机器条件跳转 |
| false label | 假分支标签 | CJUMP 的 false target |
