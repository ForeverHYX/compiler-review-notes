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

### Tiger 风格 AST 节点清单

教材 Tiger 编译器常把 AST 分成几大类：

| 类别 | 作用 | 典型节点 |
|---|---|---|
| `Var` | 左值/变量位置 | `SimpleVar`、`FieldVar`、`SubscriptVar` |
| `Exp` | 表达式 | `IntExp`、`StringExp`、`VarExp`、`OpExp`、`CallExp`、`IfExp`、`WhileExp` |
| `Dec` | 声明 | `VarDec`、`TypeDec`、`FunctionDec` |
| `Ty` | 类型语法 | `NameTy`、`RecordTy`、`ArrayTy` |

常见节点字段：

```text
SimpleVar(name)
FieldVar(var, fieldName)
SubscriptVar(var, indexExp)

OpExp(left, oper, right)
CallExp(funcName, args)
RecordExp(typeName, fields)
ArrayExp(typeName, size, init)
AssignExp(var, exp)
IfExp(test, then, else?)
WhileExp(test, body)
ForExp(var, lo, hi, body)
LetExp(decs, body)
SeqExp(expList)
```

这里 `var` 与 `exp` 要分清：`a[i]` 作为左值是 `SubscriptVar(SimpleVar(a), VarExp(SimpleVar(i)))`；如果它出现在表达式位置，还要包成 `VarExp(...)`。

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

更精确的编译器会保存 `source span`：

```text
start line/column + end line/column
```

例如 `a[i] = b + 1` 的赋值节点可以保存整个语句范围，而 `b + 1` 的 `OpExp` 保存右侧表达式范围。这样语义分析报错时可以高亮具体子表达式，而不是只报整行。

## 语义值栈如何构造 AST

在 LR/Yacc parser 中，状态栈旁边通常还有语义值栈。每次 shift 一个 token，就把 token 的语义值压栈；每次 reduce，就弹出右部语义值，执行动作，生成左部语义值。

规则：

```yacc
exp : exp '+' exp { $$ = A_OpExp($1, PLUS, $3); }
```

归约 `exp '+' exp` 时：

```text
$1 = 左边 exp 的 AST
$2 = '+' token
$3 = 右边 exp 的 AST
$$ = 新的 OpExp AST
```

如果还维护位置栈，`$$.pos` 通常取 `$1` 起点到 `$3` 终点。

## AST 遍历

后续阶段大多是递归遍历 AST：

- 语义分析：遍历 AST，同时维护符号表。
- IR 生成：把每个 AST 节点翻译成 IR 片段。
- pretty print：把 AST 打印回接近源码的形式。

递归遍历模板：

```text
visitExp(e):
  case IntExp:
    handle integer
  case VarExp:
    visitVar(e.var)
  case OpExp:
    visitExp(e.left)
    visitExp(e.right)
  case LetExp:
    enter scope
    visitDecs(e.decs)
    visitExp(e.body)
    exit scope
```

后续章节的 `transExp`、`transVar`、`transDec` 基本就是带返回值和环境参数的 AST 遍历。

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

## 练习参考答案

见 [23_练习参考答案.md](23_练习参考答案.md) 中对应章节。

## 术语中英对照

| English | 中文 | 考试提示 |
|---|---|---|
| abstract syntax | 抽象语法 | 去掉语法噪音后的结构 |
| abstract syntax tree, AST | 抽象语法树 | 后续阶段接口 |
| parse tree | 语法分析树 | 完整推导结构 |
| concrete syntax | 具体语法 | 源码表面形式 |
| semantic action | 语义动作 | parser 归约时执行 |
| semantic stack | 语义值栈 | 与状态栈并行 |
| attribute grammar | 属性文法 | 给语法符号附加属性 |
| synthesized attribute | 综合属性 | 从子节点向父节点传 |
| inherited attribute | 继承属性 | 从父/兄弟传给子节点 |
| tagged union | 带标签联合 | C 中常用 AST 表示 |
| variant | 变体 | AST 节点不同种类 |
| source position | 源码位置 | 报错定位 |
| source span | 源码范围 | 起止位置 |
| tree traversal | 树遍历 | 递归访问 AST |
| tree walking | 树遍历 | traversal 同义 |
| visitor | 访问者 | 常见遍历模式 |
| pretty printer | 美化打印器 | AST -> 可读源码 |
| Absyn | 抽象语法模块 | Appel/Tiger 常见命名 |
| constructor | 构造函数 | 创建 AST 节点 |
