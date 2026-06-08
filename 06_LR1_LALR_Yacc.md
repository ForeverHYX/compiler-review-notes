# 06 LR(1)、LALR 与 Yacc

## 本章解决什么问题

SLR 用 FOLLOW 集限制归约，但 FOLLOW 是全局近似。有些时候，`A` 在某个具体上下文下只应该在少数 lookahead 上归约。LR(1) 把 lookahead 写进 item，提高精度。

## 本章考试能力清单

- 概念题：能比较 LR(0)、SLR、LR(1)、LALR 的 reduce 条件和精度。
- 手算题：能计算 LR(1) closure 中的 `FIRST(beta a)`，能写 goto 后的 LR(1) items。
- 冲突题：能解释 LALR 合并 same core 后为什么可能产生 reduce/reduce conflict。
- 工具题：能读懂 Yacc/Bison 的 `%token`、`%union`、`%type`、`%left`、`$1`、`$$`。

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

## Yacc/Bison 基本思想

Yacc/Bison 让你写文法和语义动作，工具生成 parser。

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

`$1`、`$2`、`$3` 表示产生式右部对应的语义值，`$$` 表示左部的语义值。

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

## Error Token

Yacc 支持特殊 token `error` 做错误恢复。思路是：遇到语法错误后丢弃一些输入，直到能恢复到某个安全位置继续分析。

## 常见误区

- LR(1) item 的 lookahead 只影响归约，不是 shift 时必须匹配的符号。
- LALR 合并 core 可能引入 reduce/reduce conflict。
- Yacc 的语义动作通常在 reduce 时执行。
- 优先级声明解决的是常见表达式冲突，不是所有文法问题。
- `error` token 是 parser generator 的恢复机制，不是源语言里的普通 token。

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
| error recovery | 错误恢复 | 发现错误后继续分析 |
| error token | 错误 token | Yacc 特殊恢复符号 |
