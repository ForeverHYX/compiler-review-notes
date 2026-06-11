# 06 LR(1)、LALR 与 Yacc

## 本章解决什么问题

SLR 用 FOLLOW 集限制归约，但 FOLLOW 是全局近似。有些时候，`A` 在某个具体上下文下只应该在少数 lookahead 上归约。LR(1) 把 lookahead 写进 item，提高精度。

## 本章考试能力清单

- 概念题：能比较 LR(0)、SLR、LR(1)、LALR 的 reduce 条件和精度。
- 手算题：能计算 LR(1) closure 中的 `FIRST(beta a)`，能写 goto 后的 LR(1) items。
- 冲突题：能解释 LALR 合并 same core 后为什么可能产生 reduce/reduce conflict。
- 工具题：能读懂 Yacc/Bison 的 `%token`、`%union`、`%type`、`%left`、`$1`、`$$`。

## 本章只学到哪里

这一章接着第 05 章，只处理“更精确的 LR 和 parser generator”：

- LR(1)：item 上带一个 lookahead，归约时只看这个 lookahead。
- LALR(1)：把 LR(1) 中 core 相同的状态合并，减少状态数。
- Yacc/Bison：用声明、文法规则和语义动作生成 LALR 风格 parser。
- 冲突处理：知道默认规则、优先级/结合性声明和 `%prec` 的作用。
- 错误恢复：知道 Yacc 的 `error` token 和同步 token 思路。

本章不要求完整手画大型 LR(1) 自动机；考试重点通常是 closure/goto 中 lookahead 的传播、LALR 合并的后果、Yacc 语法和冲突规则。

## SLR 为什么还不够精确

SLR 的 reduce 条件是：

```text
A -> alpha .
lookahead in FOLLOW(A)
```

问题在于 FOLLOW(A) 是全局集合，只说明某些句型中 `A` 后面可能出现这些 token；但在某个具体 LR 状态里，当前栈前缀不一定允许所有 FOLLOW token。

PPT 的直觉是：LR 分析应当是最右推导的逆过程。即使 `x in FOLLOW(A)`，如果当前栈前缀接上 `A x` 并不是任何合法最右句型前缀，就不该按 `A -> alpha` 归约。LR(1) 的做法就是把“当前具体上下文中允许哪些 lookahead”直接写进 item。

## LR(1) Item

LR(1) item 形如：

```text
[A -> alpha . beta, a]
```

含义：正在识别 `A -> alpha beta`，点表示进度；如果最终完成并且下一个输入是 `a`，才允许归约。

完整项：

```text
[A -> alpha ., a]
```

只在 `lookahead == a` 时归约。

更完整地说，`[A -> alpha . beta, a]` 表示：

- 栈顶已经识别出 `alpha`。
- 接下来希望识别出能由 `beta a` 开头的输入。
- `a` 只在 item 完成时控制 reduce，不要求 shift 时当前输入一定是 `a`。

起始项常写成：

```text
[S' -> . S EOF, ?]
```

这里 `?` 是任意占位符，因为真正的 EOF 已经在右部里，最后不会再移进 `?`。有些写法直接用 `[S' -> . S, EOF]`，按题目给的增广文法保持一致即可。

## LR(1) Closure

如果项集中有：

```text
[A -> alpha . B beta, a]
```

则对 `B -> gamma` 加入：

```text
[B -> . gamma, b]
```

其中：

```text
b in FIRST(beta a)
```

直觉：`B` 之后会出现 `beta`，如果 `beta` 能空，再看原 item 的 lookahead `a`。

`goto` 与 LR(0) 类似：先让点越过一个符号，再对结果做 LR(1) closure。区别只是 item 上保留 lookahead。

手算 `FIRST(beta a)` 时按三种情况处理：

| `beta` 情况 | `FIRST(beta a)` 怎么看 |
|---|---|
| `beta` 以终结符 `t` 开头 | 结果就是 `{t}` |
| `beta` 以不可空非终结符开头 | 取它的 FIRST，不含 epsilon |
| `beta` 可空或为空 | 除了 `FIRST(beta)-{epsilon}`，还要把 `a` 传下去 |

如果同一个 LR(1) 状态里有多个 item 只差 lookahead，可以紧凑写成：

```text
[V -> . x, {EOF, =}]
```

它等价于：

```text
[V -> . x, EOF]
[V -> . x, =]
```

这种紧凑写法只是在同一个状态里省空间，不等于 LALR 合并。

## 例题：LR(1) Closure 手算

文法：

```text
S' -> S
S  -> A c
A  -> a
A  -> epsilon
```

初始 item：

```text
[S' -> . S, EOF]
```

closure 第一步：点后是 `S`，`beta` 为空，原 lookahead 是 `EOF`：

```text
FIRST(beta EOF) = FIRST(EOF) = { EOF }
```

加入：

```text
[S -> . A c, EOF]
```

再看 `[S -> . A c, EOF]`，点后是 `A`，`beta` 是 `c`，原 lookahead 是 `EOF`：

```text
FIRST(c EOF) = { c }
```

所以对 `A` 的每个产生式加入 lookahead `c`：

```text
[A -> . a, c]
[A -> . epsilon, c]
```

最终 closure：

```text
[S' -> . S, EOF]
[S  -> . A c, EOF]
[A  -> . a, c]
[A  -> . epsilon, c]
```

重点：`A -> epsilon` 完成后只会在 lookahead `c` 上归约，不是在所有 `FOLLOW(A)` 上归约。这就是 LR(1) 比 SLR 精确的地方。

## LR(1) 填表规则

LR(1) 构造表时，shift/goto 和 LR(0) 一样，reduce 更精确：

1. 如果状态 `I` 对终结符 `t` 有边到 `J`，填 `ACTION[I,t] = shift J`。
2. 如果状态 `I` 对非终结符 `A` 有边到 `J`，填 `GOTO[I,A] = J`。
3. 如果状态 `I` 有完整项 `[A -> alpha ., a]`，只填 `ACTION[I,a] = reduce A -> alpha`。
4. 如果增广开始产生式完成并读到 EOF，填 `accept`。

考试里最容易错的是第 3 条：LR(1) 不再看 `FOLLOW(A)`，而是看 item 自带的 lookahead。

## LR(0)、SLR、LR(1) 的归约条件对比

| 方法 | 完整项归约条件 |
|---|---|
| LR(0) | 在所有终结符上归约 |
| SLR(1) | 在 `FOLLOW(A)` 上归约 |
| LR(1) | 在 item 自带 lookahead 上归约 |

精度：`LR(1) > SLR(1) > LR(0)`。

## LALR(1)

LR(1) 状态可能很多。LALR 的做法是：

1. 构造 LR(1) 项集。
2. 找 core 相同的状态。
3. 合并它们的 lookahead 集合。

Core 指去掉 lookahead 后的 LR(0) item 集合。

例：

```text
[A -> alpha ., a]
[A -> alpha ., b]
```

合并后：

```text
[A -> alpha ., {a,b}]
```

LALR 通常比 LR(1) 状态少，表达能力接近 LR(1)，因此很多 parser generator 使用 LALR。

合并状态时，DFA 边也要随状态合并而重定向：原来指向两个旧状态的边改为指向新状态，新状态的出边合并旧状态的出边。考试一般不要求实现算法，但要知道 LALR 不是重新发明 shift/reduce 算法，而是在 LR(1) 状态基础上压缩。

常用比较：

| 方法 | 状态来源 | reduce lookahead | 状态数/能力直觉 |
|---|---|---|---|
| LR(0) | LR(0) items | 无 lookahead，完整项就归约 | 状态少，能力弱 |
| SLR(1) | LR(0) items | `FOLLOW(A)` | 状态同 LR(0)，能力更强 |
| LALR(1) | 合并 LR(1) same core | 合并后的 lookahead 集 | 状态接近 SLR，能力接近 LR(1) |
| LR(1) | 完整 LR(1) items | item 自带 lookahead | 状态多，能力最强 |

### LALR 合并为什么可能引入冲突

合并只看 core，不看 lookahead。假设两个 LR(1) 状态：

```text
I:
[A -> x ., a]
[B -> y ., b]

J:
[A -> x ., b]
[B -> y ., a]
```

它们的 core 都是：

```text
A -> x .
B -> y .
```

合并后：

```text
[A -> x ., {a,b}]
[B -> y ., {a,b}]
```

现在 lookahead `a` 和 `b` 上都同时有两个 reduce，可能产生 reduce/reduce conflict。真实文法中不一定这么简单，但考试问“为什么 LALR 合并可能引入冲突”时，核心就是 lookahead 集合合并后扩大了归约条件。

注意：如果原 canonical LR(1) 表没有冲突，合并 same core 的典型风险是引入 reduce/reduce conflict。直觉上，shift 边由 core 决定；合并主要扩大的是 reduce 的 lookahead 集。

## Yacc/Bison 基本思想

Yacc/Bison 让你写文法和语义动作，工具生成 parser。

PPT 和虎书都把 Yacc 文件看成三段：

```text
声明
%%
翻译规则
%%
辅助 C 例程
```

声明段放 token、类型、优先级、C 头部声明；规则段放产生式和语义动作；最后一段放 `yylex`、`yyerror` 或其他 C 函数。

典型结构：

```yacc
%token ID NUM
%left '+'
%left '*'

%%
exp : exp '+' exp { $$ = make_add($1, $3); }
    | exp '*' exp { $$ = make_mul($1, $3); }
    | NUM         { $$ = make_num($1); }
    ;
%%
```

`$1`、`$2`、`$3` 表示产生式右部对应的语义值，`$$` 表示左部的语义值。语义动作在 parser 按这条产生式 reduce 时执行。

更完整的 Yacc/Bison 文件通常有三段：

```yacc
%{
#include "absyn.h"
void yyerror(const char *s);
int yylex(void);
%}

%union {
  int ival;
  char *sval;
  A_exp exp;
}

%token <sval> ID
%token <ival> NUM
%type  <exp> exp

%left '+'
%left '*'

%%
exp : exp '+' exp { $$ = A_OpExp(PLUS, $1, $3); }
    | exp '*' exp { $$ = A_OpExp(TIMES, $1, $3); }
    | NUM         { $$ = A_IntExp($1); }
    | ID          { $$ = A_VarExp($1); }
    ;
%%

void yyerror(const char *s) { /* report syntax error */ }
```

| 写法 | 含义 |
|---|---|
| `%token` | 声明终结符 |
| `%union` | 声明语义值可能的 C 类型 |
| `%type` | 声明非终结符语义值类型 |
| `yylex()` | lexer 函数，返回 token |
| `yyparse()` | parser 入口函数 |
| `yyerror()` | 语法错误处理函数 |
| `%start` | 指定开始符号 |
| `%prec` | 给某条产生式指定特殊优先级 |

## Lex 与 Yacc 协作

```text
source characters -> Lex -> tokens -> Yacc parser -> AST
```

Lex 返回 token 类型和语义值。Yacc 根据 token 序列做语法分析，并在归约时执行语义动作。

## 优先级与结合性声明

二义表达式文法可以靠声明处理：

```yacc
%left '+'
%left '*'
```

越靠后的声明优先级越高。`%left` 表示左结合，`%right` 表示右结合。

冲突默认规则要知道但不要滥用：

- shift/reduce conflict 默认选择 shift。
- reduce/reduce conflict 默认选择先出现的产生式。

表达式文法最好用优先级和结合性声明显式解决：

```yacc
%left '+'
%left '*'
```

因为 `*` 声明在 `+` 后面，所以 `*` 优先级更高。`%left` 让 `a+b+c` 按 `(a+b)+c` 归约。

Yacc 处理表达式冲突时比较“待 shift 的 token”和“待 reduce 的产生式”的优先级：

- token 的优先级来自 `%left/%right/%nonassoc` 声明。
- 产生式默认使用右部最后一个终结符的优先级。
- 如果产生式优先级高，选择 reduce。
- 如果 token 优先级高，选择 shift。
- 如果优先级相同，`%left` 选 reduce，`%right` 选 shift，`%nonassoc` 产生 error。

一元负号常用 `%prec`：

```yacc
%left '+' '-'
%left '*'
%right UMINUS

%%
exp : '-' exp %prec UMINUS
    | exp '+' exp
    | exp '*' exp
    | NUM
    ;
```

`UMINUS` 不一定是 lexer 返回的 token，它可以只是优先级占位符，让 `- exp` 这条产生式使用更高优先级。

经验规则：dangling else 和常规算符优先级是可接受的冲突处理场景；大多数 shift/reduce conflict、几乎所有 reduce/reduce conflict 都应该回去检查文法，而不是盲目依赖默认规则。

## Error Token

Yacc 支持特殊 token `error` 做错误恢复。思路是：遇到语法错误后丢弃一些输入，直到能恢复到某个安全位置继续分析。

典型错误产生式：

```yacc
stmt : error ';'
     | IF exp THEN stmt
     | ID ASSIGN exp
     ;

exp : '(' error ')'
    | exp '+' exp
    | NUM
    ;
```

`error` 不是源程序里的普通 token，而是 parser generator 的特殊符号。PPT 给的 bottom-up 恢复步骤可以记成：

1. 发现语法错误。
2. 弹出分析栈，直到某个状态可以 shift `error`。
3. shift `error`。
4. 丢弃输入 token，直到遇到同步 token 或某个可继续分析的位置。
5. 按错误产生式 reduce，然后恢复正常分析。

同步 token 常选 `;`、`)`、`}` 这类结构边界。local recovery 在出错点附近修复；global recovery 会尝试更早位置的插入、删除、替换，课程里知道概念即可。

## 语法分析方法总览

| 方法 | 推导/归约方向 | 表或栈的关键 | 左递归 | 考试定位 |
|---|---|---|---|---|
| LL(1) | 自顶向下，最左推导 | `M[非终结符, lookahead]` | 不能直接处理 | FIRST/FOLLOW、预测分析表 |
| LR(0) | 自底向上，最右推导逆 | LR(0) item DFA | 可以 | item/closure/goto 入门 |
| SLR(1) | 自底向上 | LR(0) DFA + FOLLOW reduce | 可以 | 知道 FOLLOW 是全局近似 |
| LALR(1) | 自底向上 | 合并 LR(1) same core | 可以 | parser generator 常用 |
| LR(1) | 自底向上 | LR(1) item lookahead | 可以 | closure 中 `FIRST(beta a)` |

两个判断题结论：

- LL(1) 文法可以看作 LR(1) 能处理的范围内，所以“存在 LL(1) 但不是 LR(1)”为假。
- 二义文法不属于 LR(k)，但 Yacc 可以在少数明确场景下通过冲突规则使用二义文法。

## 常见误区

- LR(1) item 的 lookahead 只影响归约，不是 shift 时必须匹配的符号。
- LALR 合并 core 可能引入 reduce/reduce conflict。
- Yacc 的语义动作通常在 reduce 时执行。
- 优先级声明解决的是常见表达式冲突，不是所有文法问题。
- `error` token 是 parser generator 的恢复机制，不是源语言里的普通 token。
- LALR 的 core 是去掉 lookahead 后的 LR(0) item 集，不是只看产生式左部。
- `%prec` 改的是某条产生式的优先级，不会让 lexer 返回新 token。
- Yacc 默认 shift 可以解释 dangling else，但不代表所有 shift/reduce conflict 都安全。

## 本章覆盖核对

| PPT/教材范围 | 本章位置 | 考试掌握到什么程度 |
|---|---|---|
| SLR 局限 | `SLR 为什么还不够精确` | 能说明 FOLLOW 是全局近似 |
| LR(1) item | `LR(1) Item` | 会解释点、lookahead、起始项 |
| LR(1) closure/goto | `LR(1) Closure`、`例题：LR(1) Closure 手算` | 会算 `FIRST(beta a)` |
| LR(1) reduce action | `LR(1) 填表规则` | 完整项只在 item lookahead 上归约 |
| LR(0)/SLR/LR(1) 对比 | `LR(0)、SLR、LR(1) 的归约条件对比`、`语法分析方法总览` | 能做归约条件判断题 |
| LALR 合并 | `LALR(1)` | 会找 same core，合并 lookahead |
| LALR 冲突 | `LALR 合并为什么可能引入冲突` | 能解释 reduce/reduce 来源 |
| Yacc 三段式与语义动作 | `Yacc/Bison 基本思想` | 能读 `%token/%union/%type/$1/$$` |
| Lex/Yacc 协作 | `Lex 与 Yacc 协作` | 知道 `yylex` 给 `yyparse` token |
| 优先级/结合性 | `优先级与结合性声明` | 知道默认 shift、`%left/%right/%nonassoc/%prec` |
| 错误恢复 | `Error Token` | 知道 error token、同步 token、弹栈/丢 token 步骤 |

## 练习

1. 写出 `[A -> alpha . B beta, a]` 的 LR(1) closure 规则。
2. 比较同一完整项在 LR(0)、SLR、LR(1) 中的归约位置。
3. 给两个 core 相同但 lookahead 不同的 LR(1) 状态，合并为 LALR 状态。
4. 写一段 Yacc 规则，为加法和乘法构造 AST。

## 练习参考答案

见 [23_练习参考答案.md](23_练习参考答案.md) 中对应章节。

## 术语中英对照

| English | 中文 | 考试提示 |
|---|---|---|
| LR(1) item | LR(1) 项 | LR(0) item + lookahead |
| lookahead terminal | 向前看终结符 | 控制何时归约 |
| core | 核心 | 去掉 lookahead 的 item 集 |
| LALR parsing | LALR 分析 | 合并相同 core 的 LR(1) 状态 |
| canonical LR(1) | 规范 LR(1) | 未合并的 LR(1) 项集族 |
| reduce/reduce conflict | 归约/归约冲突 | 同 lookahead 多个 reduce |
| shift/reduce conflict | 移进/归约冲突 | 同 lookahead shift 和 reduce |
| parser generator | 语法分析器生成器 | Yacc/Bison/ANTLR |
| Yacc | Yacc 工具 | 常生成 LALR parser |
| Bison | GNU Bison | Yacc 兼容工具 |
| semantic value | 语义值 | `$1`、`$$` |
| semantic value stack | 语义值栈 | 与分析栈同步 |
| semantic action | 语义动作 | 归约时执行的代码 |
| `%union` | 语义值联合类型声明 | Bison 常用 |
| `%type` | 非终结符类型声明 | 指定语义值类型 |
| `yylex` | 词法分析入口 | parser 调用 lexer |
| `yyparse` | 语法分析入口 | Bison 生成 |
| `yyerror` | 错误报告函数 | parser 出错时调用 |
| precedence declaration | 优先级声明 | 解决表达式冲突 |
| associativity declaration | 结合性声明 | `%left`、`%right` |
| `%prec` | 指定产生式优先级 | 一元负号常用 |
| `%nonassoc` | 非结合声明 | 同级连续出现时报错 |
| error recovery | 错误恢复 | 发现错误后继续分析 |
| error token | 错误 token | Yacc 特殊恢复符号 |
| synchronizing token | 同步记号 | 如 `;`、`)`、`}` |
