# 07 抽象语法 AST

## 本章解决什么问题

Parser 可以输出 Parse Tree，但后续语义分析和 IR 生成不需要所有语法细节。AST 是更紧凑、更接近程序结构的数据表示。

例如：

```text
1 + (2 * 3)
```

Parse Tree 会包含 `E/T/F`、括号等文法节点；AST 只需：

```text
    +
   / \
  1   *
     / \
    2   3
```

## Parse Tree vs AST

| Parse Tree | AST |
|---|---|
| 直接反映文法推导 | 反映程序语义结构 |
| 节点很多 | 节点更少 |
| 适合证明输入符合文法 | 适合后续编译阶段 |
| 包含括号、辅助非终结符 | 通常删除语法噪音 |

## 语义动作构造 AST

在 Yacc 中，归约时可以执行动作生成 AST 节点：

```yacc
exp : exp '+' exp { $$ = A_OpExp(PLUS, $1, $3); }
    | NUM         { $$ = A_IntExp($1); }
    ;
```

在递归下降中，可以让每个 parse 函数返回 AST 节点：

```text
parseExp():
  left = parseTerm()
  while lookahead == '+':
    match('+')
    right = parseTerm()
    left = Add(left, right)
  return left
```

## AST 表示方式

### C tagged union

```c
typedef struct A_exp_ *A_exp;

struct A_exp_ {
  enum { A_intExp, A_opExp, A_varExp } kind;
  union {
    int intt;
    struct { A_exp left; A_oper oper; A_exp right; } op;
    A_var var;
  } u;
};
```

核心思想：用 `kind` 区分节点类型，用 `union` 存不同字段。

### 面向对象类层次

```text
Exp
  IntExp
  OpExp
  VarExp
```

### 函数式 ADT

```text
Exp = IntExp int | OpExp oper Exp Exp | VarExp var
```

## 位置信息

AST 节点通常保存源码位置，如行号、列号或字符偏移。语义错误报告需要它：

```text
line 12: undefined variable x
```

没有位置信息，错误信息会很难用。

## AST 遍历

后续阶段大多是递归遍历 AST：

- 语义分析：遍历 AST，同时维护符号表。
- IR 生成：把每个 AST 节点翻译成 IR 片段。
- pretty print：把 AST 打印回接近源码的形式。

## 例题：从 Parse Tree 到 AST

文法：

```text
E -> E + T | T
T -> T * F | F
F -> NUM | ( E )
```

输入：

```text
(1 + 2) * 3
```

AST：

```text
      *
    /   \
   +     3
  / \
 1   2
```

括号不作为节点保留，但影响树的形状。

## 常见误区

- AST 不是一定唯一，取决于语言设计和编译器实现。
- 语义动作不等于语义分析；它只是 parser 归约时执行的代码。
- AST 构造阶段通常不做完整类型检查。
- 删除括号不代表忽略括号，括号已经体现在 AST 结构中。

## 练习

1. 为 `a[i] = b + 1` 画 AST。
2. 设计 `if-then-else`、`while`、函数调用的 AST 节点字段。
3. 写出表达式文法的语义动作，用于构造二元操作 AST。
4. 说明为什么错误报告需要 AST 节点保存位置信息。

## 术语中英对照

| English | 中文 | 考试提示 |
|---|---|---|
| abstract syntax | 抽象语法 | 去掉语法噪音后的结构 |
| abstract syntax tree, AST | 抽象语法树 | 后续阶段接口 |
| parse tree | 语法分析树 | 完整推导结构 |
| concrete syntax | 具体语法 | 源码表面形式 |
| semantic action | 语义动作 | parser 归约时执行 |
| semantic stack | 语义值栈 | 与状态栈并行 |
| tagged union | 带标签联合 | C 中常用 AST 表示 |
| variant | 变体 | AST 节点不同种类 |
| source position | 源码位置 | 报错定位 |
| tree traversal | 树遍历 | 递归访问 AST |
| constructor | 构造函数 | 创建 AST 节点 |

