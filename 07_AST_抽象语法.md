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

## 本章考试能力清单

- 概念题：能区分 parse tree、concrete syntax、abstract syntax、AST。
- 构造题：能把表达式、赋值、数组访问、if/while/call 转成 Tiger 风格 AST 节点。
- 实现题：能解释 tagged union、semantic value stack、semantic action、source position/source span。
- 英文题：看到 `synthesized attribute`、`visitor`、`tree walking`、`Absyn` 能说出用途。

## 本章只学到哪里

这一章解决 parser 之后的第一个接口问题：把“能否匹配文法”变成“后续阶段能处理的程序结构”。

- 了解属性文法和 semantic action 的思想，但不要求系统掌握 Knuth 属性文法理论。
- 会解释为什么 parse tree 太啰嗦，AST 更适合语义分析和 IR 生成。
- 会看 Yacc/递归下降中 AST 是如何在语义动作里构造出来的。
- 会识别 Tiger 风格 AST 中 `Var/Exp/Dec/Ty` 的大类和常见构造函数。
- 会说明 AST 节点为什么要带 source position，以及 Yacc 中如何拿到位置。

本章不做完整类型检查、不做逃逸分析、不生成 IR；这些分别在后续语义分析、活动记录和 IR 章节展开。

## 属性文法只掌握思想

PPT 开头讲 Attribute Grammar，考试通常只要理解思想：

```text
上下文无关文法 + 属性 + 属性计算规则
```

属性可以是值、类型、作用域信息、AST 节点、IR 片段等。比如：

```text
E -> E1 + T    { E.val = E1.val + T.val }
T -> num       { T.val = num.val }
```

如果属性从子节点传到父节点，叫 synthesized attribute；如果从父节点或左边兄弟传给子节点，叫 inherited attribute。构造 AST 时最常见的是 synthesized attribute：每个右部子树先构造好，再合成父节点。

本课程后面不会要求你推导复杂属性依赖图；要会把它和 Yacc 的 `$1/$3/$$` 联系起来。

## Parse Tree vs AST

| Parse Tree | AST |
|---|---|
| 直接反映文法推导 | 反映程序语义结构 |
| 节点很多 | 节点更少 |
| 适合证明输入符合文法 | 适合后续编译阶段 |
| 包含括号、辅助非终结符 | 通常删除语法噪音 |

parse tree 又叫 concrete parse tree，它和具体文法强绑定。为了消除左递归、处理优先级或适配 LL/LR，文法可能引入 `E/T/F/E'` 这类技术性非终结符；后续语义分析不应该被这些 parser 技巧污染。

AST 是 parser 和后续阶段之间的 clean interface：parsing 的细节已经解决，但还没有做完整语义解释。后续的类型检查、IR 生成、简单优化、pretty printer、代码分析工具都可以基于 AST。

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

不要把整个编译器都写进 parser action。虽然语义动作理论上可以直接求值、生成代码甚至维护符号表，但这样会让 parser 和后续阶段强耦合，难以维护，也限制语言特性。更常见的做法是：parser 只构造 AST，语义分析和 IR 生成在 AST 上单独遍历。

两种构造方式的直觉：

| 构造位置 | 怎么构造 AST | 适合记住什么 |
|---|---|---|
| 递归下降 | parse 函数返回 AST 节点 | 调用返回时自然从子树合成父树 |
| LR/Yacc | reduce 时执行语义动作 | `$1/$3` 是右部子树，`$$` 是左部父树 |

解析结束时，开始符号的 semantic value 通常就是整棵 AST。

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

Tiger 里有几处考试容易问：

- 相邻函数声明会合成同一个 `FunctionDec(fundecList)`，这样同一组函数可以互相递归。
- 相邻类型声明会合成同一个 `TypeDec(nametyList)`，用于处理互相递归的类型。
- `a.b[i]` 这类左值是 `Var` 递归嵌套：先 `FieldVar`，再 `SubscriptVar`，最后如果作为表达式再套 `VarExp`。
- `&`、`|`、一元负号可以不单独增加 AST 节点：`e1 & e2` 可表示为 `if e1 then e2 else 0`，`e1 | e2` 可表示为 `if e1 then 1 else e2`，`-x` 可表示为 `0 - x`。
- lexer 给的是字符串，Tiger AST 常用 `S_symbol` 保存标识符；`S_symbol` 把相同名字映射到同一个符号对象，方便后续符号表比较。
- Tiger 的 `VarDec`、形参字段里会有 `escape` 信息；它严格说不是纯语法属性，但放在 Absyn 里方便后续逃逸分析和活动记录。

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

PPT 和虎书强调：如果编译器先完整构造 AST，再做语义分析，lexer 已经读到 EOF，不能再用“当前 token 位置”当错误位置。因此位置必须在构造 AST 时保存下来。

Yacc/Bison 常见做法：

- Bison 可以维护 location/position stack。
- 传统 Yacc 没有方便的位置栈时，可以定义一个空产生式非终结符 `pos`，在需要的位置记录当前 token 位置。

例：

```yacc
%union { A_exp exp; A_pos pos; }
%type <pos> pos

pos : { $$ = EM_tokPos; }

exp : exp PLUS pos exp { $$ = A_OpExp($3, A_plus, $1, $4); }
```

`pos` 放在 `PLUS` 后面，记录的是 `+` 附近的位置。不要随意把 `pos` 放到产生式最前面；空产生式过早 reduce 可能制造新的 LR 冲突。

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

PPT 中的语义值栈和状态栈并行变化：

```text
shift token:    压入 token 的语义值
reduce A -> Y1 ... Yk:
  弹出 k 个语义值作为 $1 ... $k
  执行动作生成 $$
  把 $$ 压回语义值栈
```

所以语义动作不是“额外再扫一遍 parse tree”，而是在 LR reduce 的同时自底向上合成 AST。

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
- AST 不应保留所有 `E/T/F`、逗号、括号这类 parse tree 细节。
- `Var` 和 `VarExp` 不是一回事：`Var` 表示左值结构，`VarExp` 表示把左值当表达式读。
- 连续函数/类型声明在 Tiger AST 中通常合并成一个声明节点，不是每一行都独立成一个顶层 `Dec`。

## 本章覆盖核对

| PPT/教材范围 | 本章位置 | 考试掌握到什么程度 |
|---|---|---|
| Attribute Grammar | `属性文法只掌握思想` | 会说属性、语义规则、synthesized/inherited 的直觉 |
| Semantic Action | `语义动作构造 AST`、`语义值栈如何构造 AST` | 能解释 `$1/$3/$$` 如何合成 AST |
| Parse Tree vs AST | `Parse Tree vs AST`、`例题：从 Parse Tree 到 AST` | 会删掉语法噪音但保留结构 |
| AST 的作用 | `Parse Tree vs AST`、`AST 遍历` | 知道它是 parser 和后续阶段接口 |
| AST 表示 | `AST 表示方式` | 能读 C tagged union、Java class、函数式 ADT |
| Tiger Absyn | `Tiger 风格 AST 节点清单` | 能区分 `Var/Exp/Dec/Ty` 和常见构造函数 |
| AST 构造 | `语义动作构造 AST` | 知道 top-down 返回节点、bottom-up reduce 合成节点 |
| Position | `位置信息` | 知道为什么保存 `pos`，Yacc 可用 `pos` 空产生式 |
| Tree walking | `AST 遍历` | 知道语义分析/IR 生成都是递归遍历 AST |

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
