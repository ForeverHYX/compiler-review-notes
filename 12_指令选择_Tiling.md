# 12 指令选择与 Tiling

## 本章解决什么问题

指令选择把 IR Tree 映射为目标机器指令。核心问题是：一个 IR 树节点可能对应多种指令组合，怎样选择成本较低的组合？

## Tree Pattern 与 Tile

目标机器指令可以看作覆盖 IR Tree 的小树模式。

例如：

```text
MEM(BINOP(PLUS, TEMP fp, CONST k))
```

可能对应一条带偏移寻址的 load 指令：

```text
load r, k(fp)
```

一个 pattern 覆盖 IR 树的一部分，称为 tile。指令选择就是用 tile 覆盖整棵 IR 树。

## Tiling 原则

- 每个 IR 节点都要被覆盖。
- tile 之间不能重叠。
- tile 的叶子可以连接到子树生成的临时结果。
- 大 tile 通常生成更少指令，但不一定总是全局最优。

## Maximal Munch

Maximal Munch 是贪心算法：

1. 从树根开始。
2. 选择能匹配的最大 tile。
3. 对 tile 未覆盖的子树递归。
4. 以后序方式发出指令。

优点：简单、快速。  
缺点：不保证全局最低成本。

## 动态规划指令选择

为每个节点计算“从该节点生成目标值的最低成本”。

算法思路：

```text
postorder traverse tree:
  for each node n:
    for each tile t matching at n:
      cost = tile_cost(t) + sum(best_cost(leaf_subtree))
    choose minimum cost tile for n
emit selected tiles recursively
```

动态规划能得到最优 tiling，但实现更复杂。

## Tree Grammar

复杂机器可能有多种寄存器类和寻址模式，手写 tile 会很复杂。Tree grammar 用类似文法的规则描述 tile，再由工具生成 matcher。

例：

```text
reg -> CONST
reg -> TEMP
reg -> BINOP(PLUS, reg, reg)
addr -> BINOP(PLUS, reg, CONST)
reg -> MEM(addr)
```

## 抽象汇编

在寄存器分配前，指令使用的是临时变量，不是最终物理寄存器。

一条抽象汇编通常记录：

- `assem`：指令模板。
- `dst`：定义的 temporaries。
- `src`：使用的 temporaries。
- `jumps`：可能跳到的 label。

这些信息是后面 flow graph 和 liveness analysis 的输入。

## 调用指令建模

函数调用会：

- 使用参数寄存器。
- 定义返回值寄存器。
- 破坏 caller-save 寄存器。

因此抽象汇编里要把调用对寄存器的影响建模出来，否则活跃变量分析会漏掉干涉。

## 例题：地址模式

IR：

```text
MEM(BINOP(PLUS, TEMP fp, CONST -8))
```

如果目标机器支持 `offset(base)`，可用一条指令：

```text
load r, -8(fp)
```

如果不支持复杂寻址，可能需要：

```text
t = fp + -8
load r, 0(t)
```

指令选择依赖目标机器。

## 常见误区

- 最大 tile 不等于最低成本 tile。
- TEMP tile 通常成本为 0，因为临时变量已经是一个值。
- 指令选择前还没有完成物理寄存器分配。
- CISC 机器的 tile 可能更大，RISC 机器 tile 更规则。
- CALL 不是普通表达式，必须考虑 clobber。

## 练习

1. 给一棵 IR 树和一组 tile，手工找一种合法覆盖。
2. 用 Maximal Munch 覆盖同一棵树。
3. 给 tile 成本，用动态规划求最小成本。
4. 对一条抽象汇编写出 `dst/src/jumps`。

## 练习参考答案

见 [23_练习参考答案.md](23_练习参考答案.md) 中对应章节。

## 术语中英对照

| English | 中文 | 考试提示 |
|---|---|---|
| instruction selection | 指令选择 | IR -> abstract assembly |
| tree pattern | 树模式 | 机器指令对应的 IR 小树 |
| tile | 瓷砖/覆盖片 | 覆盖 IR 子树的模式 |
| tiling | 树覆盖 | 用 tile 覆盖整棵树 |
| Maximal Munch | 最大吞噬算法 | 贪心选择最大 tile |
| dynamic programming | 动态规划 | 求最低成本 tiling |
| tree grammar | 树文法 | 用文法描述指令模式 |
| abstract assembly | 抽象汇编 | 带 temporaries 的汇编 |
| destination, dst | 目标操作数 | 指令定义的临时变量 |
| source, src | 源操作数 | 指令使用的临时变量 |
| clobber | 破坏寄存器 | call 改写 caller-save |
| addressing mode | 寻址模式 | 如 base+offset |

