# 03 语法分析基础：CFG、推导、二义性

## 本章解决什么问题

词法分析只知道一个个 Token。语法分析要判断 Token 序列能否组成合法程序结构，并构造 Parse Tree 或 AST。

例如：

```text
id = id + id * num
```

Parser 要知道这是赋值语句，右边乘法优先于加法。

## 上下文无关文法

CFG 是四元组：

```text
G = (T, N, P, S)
```

| 符号 | 含义 |
|---|---|
| `T` | 终结符集合，通常是 Token |
| `N` | 非终结符集合，表示语法类别 |
| `P` | 产生式集合 |
| `S` | 开始符号 |

例子：

```text
E -> E + T
E -> T
T -> T * F
T -> F
F -> ( E )
F -> id
```

## 推导与归约

推导是从开始符号出发，不断用产生式右部替换非终结符。

左推导：每次替换最左边的非终结符。  
右推导：每次替换最右边的非终结符。

归约是推导的反方向。LR 分析就是一种移进-归约分析，本质上在做最右推导的逆过程。

## Parse Tree 与 AST

Parse Tree 保留完整文法结构，AST 只保留后续阶段关心的结构。

表达式：

```text
1 + 2 * 3
```

AST 通常长这样：

```text
      +
    /   \
   1     *
        / \
       2   3
```

AST 不必保留所有中间非终结符，例如 `E`、`T`、`F`。

## 文法二义性

如果同一个串有两棵不同 Parse Tree，文法就是二义的。

经典二义表达式文法：

```text
E -> E + E
E -> E * E
E -> id
```

`id + id * id` 可以解释为：

```text
(id + id) * id
id + (id * id)
```

解决方法通常是重写文法，把优先级和结合性编码进去：

```text
E -> E + T | T
T -> T * F | F
F -> id | ( E )
```

这里 `*` 比 `+` 优先级高，因为乘法在更深层的 `T/F` 中生成。

## Dangling Else

文法：

```text
S -> if E then S
S -> if E then S else S
S -> other
```

对于：

```text
if E1 then if E2 then S1 else S2
```

`else` 可以归给内层 `if`，也可以归给外层 `if`。多数语言规定 `else` 归最近的未匹配 `if`。

## 例题：写 CFG

语言：由一个或多个 `a` 后跟同样多个 `b` 的串，例如 `ab`、`aabb`、`aaabbb`。

CFG：

```text
S -> a S b
S -> a b
```

推导 `aaabbb`：

```text
S => a S b => a a S b b => a a a b b b
```

## 常见误区

- RE 和 CFG 都能描述语言，但 CFG 能描述嵌套结构，RE 不能描述任意深度括号匹配。
- 二义性是文法性质，不是语言本身一定二义。
- 消除左递归是为了 LL 分析，不等于消除二义性。
- 优先级和结合性可以写进文法，也可以由 parser generator 的声明处理。

## 练习

1. 给出 `id + id * id` 在二义文法下的两棵 Parse Tree。
2. 为括号匹配语言写一个 CFG。
3. 判断下面文法是否二义，并说明原因：

```text
E -> E - E | id
```

4. 重写表达式文法，使 `-` 左结合、`*` 优先级高于 `-`。

## 练习参考答案

见 [23_练习参考答案.md](23_练习参考答案.md) 中对应章节。

## 术语中英对照

| English | 中文 | 考试提示 |
|---|---|---|
| parsing | 语法分析 | token stream -> parse tree/AST |
| syntax analysis | 语法分析 | parsing 的同义说法 |
| context-free grammar, CFG | 上下文无关文法 | `G=(T,N,P,S)` |
| terminal | 终结符 | 通常是 Token |
| nonterminal | 非终结符 | 语法变量 |
| production | 产生式 | `A -> alpha` |
| start symbol | 开始符号 | 推导起点 |
| derivation | 推导 | 从开始符号生成串 |
| reduction | 归约 | 推导的反方向 |
| leftmost derivation | 最左推导 | 每次替换最左非终结符 |
| rightmost derivation | 最右推导 | 每次替换最右非终结符 |
| parse tree | 语法分析树 | 完整文法结构 |
| abstract syntax tree, AST | 抽象语法树 | 精简语法结构 |
| ambiguity | 二义性 | 同一串有多棵 parse tree |
| precedence | 优先级 | `*` 高于 `+` |
| associativity | 结合性 | 左结合/右结合 |
| dangling else | 悬挂 else | else 归属歧义 |

