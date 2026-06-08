# 10 IR Tree 与中间代码生成

## 本章解决什么问题

AST 还很接近源语言，不适合直接生成机器代码。中间表示把不同源语言统一到较低层结构，也让后端可以复用。

## 本章考试能力清单

- 概念题：能解释 Tree IR 节点、MEM 的 load/store 双重语义、l-value/r-value。
- 手算题：能把 assignment、if、while、for、array access 翻译成带 LABEL/CJUMP/JUMP/MOVE 的 IR。
- 形态题：能区分 Ex/Nx/Cx，并写出 Cx 到 Ex/Nx 的转换模板。
- 英文题：看到 `fragment`、`external call`、`hidden static-link argument`、`field offset` 能知道怎么翻译。

## 为什么需要 IR

如果每种源语言直接翻译到每种目标机器，需要 `N*M` 个翻译器。用 IR 后：

```text
N 个前端 -> IR -> M 个后端
```

复杂度接近 `N+M`。

## Tree IR 节点

表达式节点：

| 节点 | 含义 |
|---|---|
| `CONST(i)` | 常量 |
| `NAME(l)` | 标签地址 |
| `TEMP(t)` | 临时变量 |
| `BINOP(op,e1,e2)` | 二元运算 |
| `MEM(e)` | 内存地址 `e` 处的值 |
| `CALL(f,args)` | 函数调用 |
| `ESEQ(s,e)` | 先执行语句 `s`，再求表达式 `e` |

语句节点：

| 节点 | 含义 |
|---|---|
| `MOVE(dst,src)` | 赋值 |
| `EXP(e)` | 只为副作用求值 |
| `JUMP(e,labels)` | 无条件跳转 |
| `CJUMP(op,e1,e2,t,f)` | 条件跳转 |
| `SEQ(s1,s2)` | 顺序执行 |
| `LABEL(l)` | 标签 |

## MEM 的双重语义

`MEM(e)` 在右侧表示 load：

```text
TEMP t <- MEM(addr)
```

在 `MOVE(MEM(addr), value)` 左侧表示 store：

```text
MEM(addr) <- value
```

这是常见考点。

## Ex、Nx、Cx

源语言中很多东西都叫表达式，但翻译到 IR 时有三种形态：

| 形态 | 含义 | 例子 |
|---|---|---|
| `Ex` | 产生一个值 | `a + b` |
| `Nx` | 只产生副作用，不产生值 | `while`、赋值语句 |
| `Cx` | 条件表达式，用跳转表示真假 | `a < b`、短路逻辑 |

条件表达式不一定先算出 `0/1`，更常用跳转表达：

```text
if a < b goto trueLabel else falseLabel
```

### Ex/Nx/Cx 转换

有时后续上下文需要另一种形态，可以转换：

| 从 | 到 | 思路 |
|---|---|---|
| `Ex` -> `Nx` | `EXP(e)` | 只保留副作用，丢弃值 |
| `Cx` -> `Nx` | 生成 true/false label | 条件只用于控制流 |
| `Cx` -> `Ex` | 生成临时变量 `r` | true 分支令 `r=1`，false 分支令 `r=0` |
| `Nx` -> `Ex` | 通常不自然 | 没有值，除非人为返回 0 |

`Cx -> Ex` 的典型模板：

```text
r := 1
Cx(cond, trueLabel, falseLabel)
LABEL falseLabel
r := 0
LABEL trueLabel
TEMP r
```

真实实现会更小心地放置 join label，但核心是“用控制流给临时变量赋真假值”。

### Patch List / Backpatching

为了先生成条件跳转、后补目标 label，编译器常让 `Cx` 保存两个待填列表：

```text
Cx = {
  stm: CJUMP(op, left, right, ?, ?),
  trues: 需要填 true label 的位置,
  falses: 需要填 false label 的位置
}
```

当外层 `if` 或 `while` 知道 true/false label 后，再把这些洞补上。这叫 backpatching。它让短路表达式和条件跳转的组合更自然。

## 短路求值

`a && b` 不能简单翻译成：

```text
t1 = eval(a)
t2 = eval(b)
t3 = t1 && t2
```

因为如果 `a` 为假，`b` 不应被求值。正确思路是控制流：

```text
if a goto check_b else false
check_b:
if b goto true else false
```

## 变量访问与 Static Link

访问当前 frame 中变量：

```text
MEM(FP + offset)
```

访问外层变量：

```text
fp1 = MEM(FP + static_link_offset)
fp2 = MEM(fp1 + static_link_offset)
MEM(fp2 + var_offset)
```

沿 static link 走多少步由词法嵌套层级决定。

## Tiger AST 到 Tree IR 翻译规则总表

| AST | IR 翻译直觉 |
|---|---|
| `IntExp(i)` | `CONST(i)` |
| `StringExp(s)` | 生成 string fragment，表达式为 `NAME(label)` |
| `VarExp(v)` | 翻译变量地址/访问，得到 `Ex` |
| `OpExp(a,+,b)` | `BINOP(PLUS, unEx(a), unEx(b))` |
| 比较表达式 | `Cx(CJUMP(op, unEx(a), unEx(b), t, f))` |
| `AssignExp(var,e)` | `Nx(MOVE(varAccess, unEx(e)))` |
| `SeqExp(e1;...;en)` | 前面表达式转 `Nx`，最后一个保留值 |
| `IfExp(test,then,else)` | 用 `Cx` 分支和 join label；有值时用临时变量收集结果 |
| `WhileExp(test,body)` | `test/body/done` 三个 label；`break` 跳 `done` |
| `ForExp(i,lo,hi,body)` | 降成带 limit 临时变量的 while |
| `CallExp(f,args)` | `CALL(NAME f_label, staticLink :: args)` |
| `RecordExp` | 调 runtime 分配对象，再按字段 offset 写入 |
| `ArrayExp` | 调 runtime 初始化数组 |
| `LetExp(decs,body)` | 声明产生初始化语句，再接 body |

`unEx/unNx/unCx` 是把 `Tr_exp` 强制转换为需要形态的接口。考试看到这些名字，要知道它们不是源语言函数，而是翻译模块内部工具。

## 控制结构翻译

### if-then-else

```text
Cx(condition, trueLabel, falseLabel)
LABEL trueLabel
  then body
JUMP join
LABEL falseLabel
  else body
LABEL join
```

### while

```text
LABEL test
  condition ? body : done
LABEL body
  body stm
  JUMP test
LABEL done
```

`break` 翻译为跳到当前循环的 `done` 标签。

### for 循环翻译直觉

`for i := lo to hi do body` 常降成类似 while：

```text
i := lo
limit := hi
LABEL test
if i <= limit goto body else done
LABEL body
body
if i < limit goto incr else done
LABEL incr
i := i + 1
JUMP test
LABEL done
```

要把 `hi` 保存到临时变量，避免每次迭代重复求值，也避免 `hi` 表达式有副作用时语义改变。

## Fragment

编译结果可能包含多类片段：

- 字符串常量片段。
- 函数过程片段。

后端最终把这些片段汇总为目标汇编。

字符串片段示例：

```text
StringFrag(label=L_str0, value="hello")
```

过程片段示例：

```text
ProcFrag(body=Tree IR statements, frame=f_frame)
```

函数调用外部 runtime 时常生成 `external call`，例如：

```text
CALL(NAME "initArray", [size, init])
CALL(NAME "allocRecord", [bytes])
```

## 例题：数组访问

表达式：

```text
a[i]
```

如果 `a` 已经是数组基地址，元素大小为 4：

```text
MEM(a + i * 4)
```

但在 Tiger 翻译里，局部变量 `a` 通常不是“基地址本身的名字”，而是一个变量访问位置。若 `a` 是存在 frame 里的数组变量，先要读出数组指针：

```text
a_ptr = MEM(FP + a_offset)
addr  = BINOP(PLUS, a_ptr, BINOP(MUL, i, CONST wordSize))
MEM(addr)
```

如果数组对象头部还保存长度，元素起始地址可能要跳过 header：

```text
MEM(a_ptr + headerSize + i * wordSize)
```

若语言安全，还要加入 bounds check：

```text
if i < 0 goto error
if i >= length(a) goto error
MEM(base(a) + i * 4)
```

## 常见误区

- IR 是树，不是一定等于三地址码。
- `ESEQ` 很方便生成，但后面要规范化掉。
- 条件表达式常用跳转而不是布尔值。
- `CALL` 有副作用，会影响规范化和寄存器调用约定。
- 数组/record 通常是指针，访问字段是地址计算再 `MEM`。

## 练习

1. 把 `x := a + b * c` 翻译成 Tree IR。
2. 把 `if a < b then x := 1 else x := 2` 翻译为带 label 的 IR。
3. 写出 `while i < n do i := i + 1` 的 IR 控制流。
4. 解释 `Ex/Nx/Cx` 三者如何互相转换。

## 练习参考答案

见 [23_练习参考答案.md](23_练习参考答案.md) 中对应章节。

## 术语中英对照

| English | 中文 | 考试提示 |
|---|---|---|
| intermediate representation, IR | 中间表示 | 前后端桥梁 |
| IR tree | IR 树 | 教材 Tree 表示 |
| temporary | 临时变量 | `TEMP(t)` |
| label | 标签 | 跳转目标 |
| memory access | 内存访问 | `MEM(e)` |
| load | 读内存 | `MEM` 在右侧 |
| store | 写内存 | `MOVE(MEM(...),...)` |
| side effect | 副作用 | 改变状态 |
| conditional jump | 条件跳转 | `CJUMP` |
| short-circuit evaluation | 短路求值 | 用控制流表示 |
| fragment | 片段 | 字符串或过程输出 |
| proc fragment | 过程片段 | 函数体和 frame |
| string fragment | 字符串片段 | 字符串常量数据 |
| external call | 外部调用 | 调 runtime 函数 |
| hidden static-link argument | 隐藏 static link 参数 | 函数调用额外实参 |
| field offset | 字段偏移 | record 字段位置 |
| base address | 基地址 | array/record 起始地址 |
| word size | 字长 | offset 计算单位 |
| unEx / unNx / unCx | 形态转换 | translate 模块接口 |
| l-value | 左值 | 可被赋值的位置 |
| r-value | 右值 | 表达式的值 |
