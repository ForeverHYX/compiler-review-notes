# 06 LR(1)、LALR 与 Yacc

## 本章解决什么问题

SLR 用 FOLLOW 集限制归约，但 FOLLOW 是全局近似。有些时候，`A` 在某个具体上下文下只应该在少数 lookahead 上归约。LR(1) 把 lookahead 写进 item，提高精度。

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

## 术语中英对照

| English | 中文 | 考试提示 |
|---|---|---|
| LR(1) item | LR(1) 项 | LR(0) item + lookahead |
| lookahead terminal | 向前看终结符 | 控制何时归约 |
| core | 核心 | 去掉 lookahead 的 item 集 |
| LALR parsing | LALR 分析 | 合并相同 core 的 LR(1) 状态 |
| parser generator | 语法分析器生成器 | Yacc/Bison/ANTLR |
| Yacc | Yacc 工具 | 常生成 LALR parser |
| Bison | GNU Bison | Yacc 兼容工具 |
| semantic value | 语义值 | `$1`、`$$` |
| semantic action | 语义动作 | 归约时执行的代码 |
| precedence declaration | 优先级声明 | 解决表达式冲突 |
| associativity declaration | 结合性声明 | `%left`、`%right` |
| error recovery | 错误恢复 | 发现错误后继续分析 |
| error token | 错误 token | Yacc 特殊恢复符号 |

