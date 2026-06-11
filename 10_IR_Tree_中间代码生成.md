# 10 IR Tree 与中间代码生成

## 本章解决什么问题

AST 还很接近源语言，不适合直接生成机器代码。中间表示把不同源语言统一到较低层结构，也让后端可以复用。

## 本章考试能力清单

- 概念题：能解释 Tree IR 节点、MEM 的 load/store 双重语义、l-value/r-value。
- 手算题：能把 assignment、if、while、for、array access 翻译成带 LABEL/CJUMP/JUMP/MOVE 的 IR。
- 形态题：能区分 Ex/Nx/Cx，并写出 Cx 到 Ex/Nx 的转换模板。
- 英文题：看到 `fragment`、`external call`、`hidden static-link argument`、`field offset` 能知道怎么翻译。

## 本章只学到哪里

PPT 先讲 IR 的意义，再讲 Tiger 采用的 IR Tree，最后讲 AST 到 IR Tree 的翻译。本章重点是“会读、会画、会翻译小程序”，不是提前学习第 11 章的 canonicalization，也不是学习 LLVM SSA 优化。

考试范围可按三层记：

1. IR 为什么存在：前端/中端/后端解耦。
2. IR Tree 节点语义：`MEM`、`MOVE`、`CALL`、`CJUMP`、`ESEQ` 等。
3. Tiger 翻译套路：`Ex/Nx/Cx`、变量地址、static link、数组/record、条件和循环、function call、declaration、fragment。

## 为什么需要 IR

如果每种源语言直接翻译到每种目标机器，需要 `N*M` 个翻译器。用 IR 后：

```text
N 个前端 -> IR -> M 个后端
```

复杂度接近 `N+M`。

PPT 中还提到 IR 可以按抽象层次分为 high-level IR、middle-level IR、low-level IR，也可以按结构分为 tree/DAG/linear/hybrid。考试通常不要求背分类细节，只要知道：

- Tree IR 是结构化表示，适合从 AST 生成。
- 三地址码是线性表示，适合说明“每条指令很简单”。
- CFG 是混合表示，节点内线性、节点间成图。

三地址码的一般形式：

```text
x = y op z
```

例：

```text
x + y * z

t1 = y * z
t2 = x + t1
```

Tiger 课上真正展开的是 IR Tree，不是让你用三地址码做完整翻译。

## Tree IR 节点

Tiger compiler 使用一种低层 tree representation。它在 AST 和 assembly 之间：

```text
AST -> IR Tree -> assembly -> machine code
```

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

`TEMP(t)` 可以看成抽象机器中的寄存器。它是无限多个 temporary；真正有限的物理寄存器分配放到后面的 register allocation。

常见 `BINOP`：

```text
PLUS, MINUS, MUL, DIV
AND, OR, XOR
LSHIFT, RSHIFT, ARSHIFT
```

语句节点：

| 节点 | 含义 |
|---|---|
| `MOVE(dst,src)` | 赋值 |
| `EXP(e)` | 只为副作用求值 |
| `JUMP(e,labels)` | 无条件跳转 |
| `CJUMP(op,e1,e2,t,f)` | 条件跳转 |
| `SEQ(s1,s2)` | 顺序执行 |
| `LABEL(l)` | 标签 |

常见 `CJUMP` relational operator：

```text
EQ, NE, LT, GT, LE, GE
ULT, ULE, UGT, UGE   // unsigned comparisons，了解即可
```

注意 `NAME(L)` 和 `LABEL(L)` 的区别：

- `NAME(L)` 是表达式，表示“标签 `L` 的地址/符号常量”，常作为 `JUMP` 或 `CALL` 目标。
- `LABEL(L)` 是语句，表示“这里定义标签 `L`”。

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

`ESEQ(s,e)` 的语义是先执行 `s` 的副作用，再求 `e` 的值。例如：

```text
ESEQ(MOVE(TEMP a, CONST 5),
     BINOP(PLUS, TEMP a, CONST 5))
```

结果是 10。`ESEQ` 方便翻译，但会让求值顺序复杂，所以第 11 章会把它规范化掉。

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

`Nx -> Ex` 在虎书 `unEx` 中也可以人为翻成：

```text
ESEQ(nx_statement, CONST 0)
```

这只表示“先执行副作用，再给一个无意义的 0”。不要把它理解为源程序真的返回 0。

`Ex -> Cx` 常见模板是把非 0 当真：

```text
CJUMP(NE, unEx(e), CONST 0, trueLabel, falseLabel)
```

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

虎书中 `Cx` 内部大致是：

```text
struct Cx {
  patchList trues;
  patchList falses;
  T_stm stm;
}
```

`doPatch(list, label)` 把列表中的洞都填成同一个 label；`joinPatch(a,b)` 合并待填列表。

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

更准确地说，`Semant` 不直接构造 `MEM`；它调用 `Translate`。`Translate` 再通过 `Frame` 的接口把 `F_access` 变成 Tree 表达式：

```text
F_Exp(access, frame_pointer_exp)
```

如果变量在当前 level 的 frame 中：

```text
F_Exp(InFrame(k), TEMP FP)
  = MEM(BINOP(PLUS, TEMP FP, CONST k))
```

如果变量是 `InReg(t)`，`frame_pointer_exp` 会被忽略，结果就是 `TEMP t`。

访问外层变量时，传给 `F_Exp` 的不是当前 `TEMP FP`，而是沿 static link 走到变量声明 level 的 frame pointer。

## L-value 与 R-value

PPT 这里专门区分：

| 概念 | 含义 | 例子 |
|---|---|---|
| r-value | 可计算出的值，不能作为赋值目标 | `a + 3`、`CONST 5` |
| l-value | 可赋值的位置，也可在右侧取其内容 | `x`、`a[i]`、`r.field` |

考试问“不符合 left value 的选项”，`BINOP(ADD, CONST(1), CONST(2))` 这种纯计算表达式不是 l-value；`TEMP x` 和 `MEM(...)` 可以作为 `MOVE` 左侧。

Tiger 没有 C/Pascal 那种 structured l-value。Tiger 的 array/record 变量本质上都是一个 word 的指针，赋值复制指针，不复制整个对象。

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

### 算术与比较

算术二元运算通常直接对应 `BINOP`：

```text
a + b  -> BINOP(PLUS, unEx(a), unEx(b))
a - b  -> BINOP(MINUS, unEx(a), unEx(b))
```

Tree IR 没有专门的一元负号。Tiger 的 `-x` 可翻译成：

```text
BINOP(MINUS, CONST 0, unEx(x))
```

比较表达式通常是 `Cx`：

```text
a < b -> Cx(CJUMP(LT, unEx(a), unEx(b), true?, false?))
```

字符串相等不是简单 `EQ` 指针比较，而应调用 runtime 函数，例如 `stringEqual(a,b)`，因为需要逐字符比较内容。

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

PPT/虎书还提醒一个细节：如果 `limit = maxint`，循环体后直接做 `i := i + 1` 可能溢出。因此常见安全模板是在递增前判断 `i < limit`：

```text
if lo > hi goto done
i := lo
limit := hi
LABEL test
body
if i >= limit goto done
i := i + 1
JUMP test
LABEL done
```

不同教材排 label 的方式可能略有差别，核心是：`hi` 只求一次，并避免在 `i == maxint` 时执行 `i + 1`。

## Record、Array、String 翻译

### Record

Tiger record 是堆对象，变量里保存指针。创建 record 的直觉：

```text
r := externalCall("allocRecord", [field_count * wordSize])
MEM(r + 0 * W) := field0
MEM(r + 1 * W) := field1
...
result = r
```

Tree 里常用 `ESEQ` 表达“先分配和初始化字段，再返回指针”：

```text
ESEQ(
  SEQ(
    MOVE(TEMP r, externalCall("allocRecord", [CONST bytes])),
    SEQ(MOVE(MEM(BINOP(PLUS, TEMP r, CONST 0)), field0),
        MOVE(MEM(BINOP(PLUS, TEMP r, CONST W)), field1))),
  TEMP r)
```

record 字段访问 `r.f_n`：

```text
MEM(BINOP(PLUS, unEx(r), CONST(n * W)))
```

如果 `r` 是存在 frame 中的变量，`unEx(r)` 本身会先把 record 指针从变量位置取出。

### Array

Tiger array 也是堆对象，变量里保存数组指针。创建数组通常调 runtime：

```text
externalCall("initArray", [size, init])
```

数组访问：

```text
a[i] -> MEM(BINOP(PLUS,
                  array_pointer,
                  BINOP(MUL, index, CONST wordSize)))
```

安全语言可加入 bounds check。PPT/考试中的常见计算通常先不展开 runtime bounds-check，除非题目明确要求。

### String

字符串字面量不是运行时每次创建，而是生成 string fragment：

```text
StringFrag(label=L_str0, value="hello")
StringExp("hello") -> NAME(L_str0)
```

虎书中的 Tiger 字符串表示可理解为：指针指向一段内存，开头一个 word 存长度，后面存字符数据。考试通常只要知道字符串字面量会变成带 label 的 data fragment，字符串操作调用 runtime。

### External Call

调用 runtime 函数不要手写目标机器细节，应通过 Frame 接口封装：

```text
F_externalCall("initArray", [size, init])
F_externalCall("allocRecord", [bytes])
```

这样可以隐藏 C 函数标签前缀、调用约定、是否需要 static link 等机器相关细节。

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

Tree IR 本身没有“函数定义”节点。一个 Tiger 函数会输出一个 `ProcFrag(body, frame)`；字符串常量输出 `StringFrag(label, value)`。最后后端遍历 fragment list 生成汇编。

## Declaration 翻译

### Variable Declaration

变量声明做两件事：

1. 在当前 frame 或 temporary 中分配位置。
2. 在 `let` body 前执行初始化。

例：

```tiger
let
  var x := 10
  var y := x + 5
in
  x + y
end
```

可理解为：

```text
ESEQ(
  SEQ(MOVE(access(x), CONST 10),
      MOVE(access(y), BINOP(PLUS, access(x), CONST 5))),
  BINOP(PLUS, access(x), access(y)))
```

### Type Declaration

类型声明只影响 `TEnv`，不产生运行时 IR：

```text
type t = {x:int}
```

翻译结果可看作 no-op。

### Function Declaration

function declaration 会产生一个独立的 `ProcFrag`，而不是把函数定义嵌到当前表达式树里。

PPT/虎书列出函数汇编段的结构：

| 序号 | 内容 |
|---|---|
| 1 | 伪指令：标记函数开始 |
| 2 | 函数入口 label |
| 3 | 调整 SP，分配 frame |
| 4 | 保存 escaping arguments，包括 static link；非逃逸参数移到 temporary |
| 5 | 保存用到的 callee-save registers / return address |
| 6 | 翻译后的函数 body |
| 7 | 把函数结果移动到 return-value register |
| 8 | 恢复 callee-save registers |
| 9 | 恢复 SP，弹出 frame |
| 10 | return/jump to return address |
| 11 | 伪指令：标记函数结束 |

其中 1、3、9、11 常依赖最终 frame size 或目标汇编格式，会在后端较晚阶段补全。`Translate` 阶段通常生成 body，并调用类似 `procEntryExit1` 的接口处理 view shift 和返回值位置。

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
- `NAME(L)` 是使用 label 的地址，`LABEL(L)` 是定义 label。
- Tiger 的 array/record assignment 是 pointer assignment，不是整块复制。
- 类型声明不生成 IR；函数声明生成 `ProcFrag`。

## 本章覆盖核对

| PPT/教材点 | 笔记位置 | 考试掌握标准 |
|---|---|---|
| IR 的作用 | 为什么需要 IR | 能解释 `N*M` 到 `N+M` 的动机 |
| IR 分类和三地址码 | 为什么需要 IR | 知道 tree/linear/hybrid，三地址码只作对照 |
| Tree IR 表达式和语句 | Tree IR 节点 | 能说每个节点语义 |
| `MEM`、`ESEQ`、side effect | MEM 的双重语义 | 能判断 load/store 和副作用 |
| Ex/Nx/Cx | Ex、Nx、Cx | 能按上下文选形态 |
| patch list/backpatching | Patch List / Backpatching | 知道先留洞、后补 label |
| static link variable access | 变量访问与 Static Link | 能沿 static link 构造 `MEM` 链 |
| l-value/r-value | L-value 与 R-value | 能判断哪些表达式能放 `MOVE` 左侧 |
| array/record pointer model | L-value 与 R-value、Record/Array/String 翻译 | 知道赋值复制指针 |
| subscripting/field selection | 例题：数组访问、Record/Array/String 翻译 | 能写 `base + index*W` 和字段 offset |
| conditionals/short-circuit | 短路求值、控制结构翻译 | 能用 `CJUMP/LABEL/JUMP` 翻译 |
| while/for/break | 控制结构翻译 | 能画 `test/body/done` 和 `break -> done` |
| function call static link | Tiger AST 到 Tree IR 翻译规则总表 | 能把 hidden static link 放入参数列表 |
| variable/type/function declarations | Declaration 翻译 | 能说 var 初始化、type no-op、function ProcFrag |
| fragments/external calls | Fragment、External Call | 能区分 `StringFrag`、`ProcFrag`、runtime call |

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
| three-address code | 三地址码 | 线性 IR 对照 |
| IR tree | IR 树 | 教材 Tree 表示 |
| temporary | 临时变量 | `TEMP(t)` |
| label | 标签 | 跳转目标 |
| `NAME` | 标签地址表达式 | 使用 label |
| `LABEL` | 标签定义语句 | 定义 label |
| memory access | 内存访问 | `MEM(e)` |
| load | 读内存 | `MEM` 在右侧 |
| store | 写内存 | `MOVE(MEM(...),...)` |
| side effect | 副作用 | 改变状态 |
| patch list | 补丁列表 | `Cx` 中待填 label 的洞 |
| backpatching | 回填 | 知道 label 后填补跳转目标 |
| conditional jump | 条件跳转 | `CJUMP` |
| short-circuit evaluation | 短路求值 | 用控制流表示 |
| fragment | 片段 | 字符串或过程输出 |
| proc fragment | 过程片段 | 函数体和 frame |
| string fragment | 字符串片段 | 字符串常量数据 |
| external call | 外部调用 | 调 runtime 函数 |
| hidden static-link argument | 隐藏 static link 参数 | 函数调用额外实参 |
| field offset | 字段偏移 | record 字段位置 |
| base address | 基地址 | array/record 起始地址 |
| pointer assignment | 指针赋值 | Tiger array/record 赋值复制指针 |
| structured l-value | 结构化左值 | C/Pascal 的大对象左值，Tiger 无 |
| word size | 字长 | offset 计算单位 |
| unEx / unNx / unCx | 形态转换 | translate 模块接口 |
| l-value | 左值 | 可被赋值的位置 |
| r-value | 右值 | 表达式的值 |
