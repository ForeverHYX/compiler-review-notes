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

## Trace Scheduling

Trace 是把可能连续执行的 basic blocks 串起来。目标是减少无用跳转，并让 `CJUMP` 的 false label 紧跟在后面。

对 `CJUMP(op,a,b,t,f)`：

1. 如果下一个块就是 `f`，很好。
2. 如果下一个块是 `t`，可以反转条件，交换 `t/f`。
3. 如果都不是，插入一个新的 false label 和 jump。

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
| linearize | 线性化 | Tree -> 语句列表 |
| basic block | 基本块 | 单入口单出口语句序列 |
| trace | 执行迹 | 可能连续执行的块序列 |
| trace scheduling | Trace 调度 | 重排基本块 |
| fall-through | 顺序落下 | 不跳转直接执行下一条 |
| side effect | 副作用 | 影响求值顺序 |
| commute | 可交换 | 判断语句和表达式能否换序 |
| conditional branch | 条件分支 | 机器条件跳转 |
| false label | 假分支标签 | CJUMP 的 false target |

