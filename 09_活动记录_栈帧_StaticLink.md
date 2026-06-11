# 09 活动记录、栈帧与 Static Link

## 本章解决什么问题

函数调用不是简单跳转。调用时必须保存返回地址、参数、局部变量、临时值和部分寄存器。活动记录就是一次函数调用在运行时占用的一块栈空间，也叫栈帧。

## 本章考试能力清单

- 概念题：能解释 activation record、FP/SP、calling convention、caller-save/callee-save。
- 手算题：能判断变量是否 escape，能画 static link/dynamic link，能计算访问外层变量要沿 static link 走几次。
- 实现题：能说明 Level、Access、Formals、hidden static link parameter、view shift、prologue/epilogue。
- 英文题：看到 `nonlocal variable`、`lexical level`、`return-value register` 能知道它们在栈帧中的作用。

## 本章只学到哪里

本章从抽象语法和语义检查转向运行时环境。PPT 的顺序是：

1. 程序运行时的 code/data 分布。
2. 函数调用为什么需要 activation record。
3. 哪些数据能放寄存器，哪些必须放 stack frame。
4. nested functions 如何访问非局部变量。
5. Tiger 编译器用 `Frame`/`Translate` 抽象隐藏机器细节。

考试复习不需要背某个真实 ABI 的所有寄存器编号，但要能读懂 caller/callee-save、FP/SP、static link、display、lambda lifting 这些概念，并能在小程序上手算。

## 运行时内存区域

```text
高地址
+------------------+
| stack            |  函数调用、局部变量
|        ↓         |
|                  |
|        ↑         |
| heap             |  动态分配对象
+------------------+
| static data      |  全局变量、字符串常量
+------------------+
| code             |  程序指令
+------------------+
低地址
```

栈用于短生命周期的调用信息；堆用于生命周期不由调用栈决定的对象。

PPT 中把运行时环境拆成 code 和 data：

| 区域 | 存什么 | 复习要点 |
|---|---|---|
| code area | 目标代码/机器指令 | 通常固定大小，只读 |
| static data | 全局变量、字符串常量等固定地址数据 | Tiger 字符串常量可看作 global/static data |
| stack | 当前活跃过程的 activation records | LIFO，函数返回时释放当前 frame |
| heap | 动态分配对象 | Tiger record/array 内容在 heap，可能比创建它的过程活得更久 |

全局变量不能放在某次调用的 activation record 中，因为所有引用都指向同一个对象。堆对象也不能只放在当前 frame 中，因为它可能在当前函数返回后仍然存在。

## 栈帧里有什么

典型栈帧：

```text
| incoming arguments |
| return address     |
| old frame pointer  |
| static link        |
| saved registers    |
| local variables    |
| outgoing arguments |
```

具体布局依赖目标机器和调用约定。

每一次函数调用都会创建一个新的 activation。例如递归函数 `f` 连续调用 `f(3) -> f(6) -> f(12)` 时，三个调用同时活跃，每个调用都有自己的参数 `x` 和局部变量 `y`。这是为什么 activation record 必须是“每次调用一份”，而不是“每个函数一份”。

栈帧能成立的关键假设是：局部变量在函数返回时可以销毁。支持 nested functions 但不支持函数作为值返回时，static link 加 stack frame 通常够用；如果语言允许函数值返回或长期保存，就需要 closure，相关内容放在后半教材拓展里理解即可。

## FP 与 SP

- `SP` 指向当前栈顶，随着 push/pop 或分配局部空间变化。
- `FP` 指向当前栈帧中一个稳定位置，用于访问固定偏移的参数和局部变量。

初学者最容易混淆：运行时地址是动态的，但相对 `FP` 的偏移可以编译期确定。

PPT 里还给出一个常见入口/出口形状：

```text
prologue:
  save old FP
  FP = SP
  SP = SP - frame_size

epilogue:
  SP = FP
  restore old FP
  return
```

实际优化编译器可能省略专门的 FP，但考试里按 PPT/虎书模型保留 FP，更容易计算偏移。

## 调用约定

调用约定规定函数调用时双方如何协作：

- 参数放寄存器还是栈？
- 返回值放哪里？
- 哪些寄存器由 caller 保存？
- 哪些寄存器由 callee 保存？
- 栈帧如何建立和销毁？

### Caller-save 与 Callee-save

| 类型 | 谁负责保存 | 适合保存什么 |
|---|---|---|
| caller-save | 调用者 | 调用后不一定还需要的临时值 |
| callee-save | 被调用者 | 调用前后必须保持的寄存器 |

caller-save/callee-save 不是硬件自动决定的，而是 calling convention 的约定。PPT 中的直觉：

- caller-save：如果 caller 在 call 之后还要用某寄存器里的值，就在 call 前保存、call 后恢复。
- callee-save：callee 如果要改这个寄存器，就在入口保存、出口恢复。

现代机器常把前几个参数放在寄存器里，返回值也常放在指定寄存器里。这样能减少内存流量，但会引出一个问题：如果某个参数寄存器在调用子函数时又要拿来传参，原值是否需要保存？答案取决于活跃性和调用约定。

减少额外保存的常见办法：

| 情况 | 为什么能少存 |
|---|---|
| 变量在 call 点之后不再 live | 可以直接覆盖对应寄存器 |
| leaf procedure | 不调用其他函数，参数常能一直留在寄存器 |
| 全局/跨过程寄存器分配 | 不同函数可约定用不同寄存器传递或保留值 |
| register windows | 每次调用切换一组寄存器，PPT 只作了解 |

这些内容和后面的 liveness/register allocation 会接上。本章只要知道：能放寄存器不等于永远不用 frame，call 点可能迫使值暂存到 frame 或其他寄存器。

## Escape 分析

变量不一定都放在栈帧。若变量不会逃逸，可以放在寄存器中。

变量逃逸的常见情况：

- 被内层函数引用。
- 地址被取出。
- 生命周期超过当前作用域。
- 需要通过引用传递。

### Escape 分析算法

对 AST 做一次遍历，给每个变量声明记录声明所在词法深度 `declDepth`：

```text
traverseExp(exp, depth):
  遇到变量声明 var x:
    记录 x.declDepth = depth
    先假设 x.escape = false
    遍历初始化表达式

  遇到函数声明 function f(...):
    参数 declDepth = depth + 1
    遍历函数体时 depth + 1

  遇到变量使用 x:
    如果 currentDepth > x.declDepth:
      x.escape = true
```

直觉：如果变量在更深的内层函数中被使用，当前函数返回前后都可能需要通过 static link 访问它，因此不能只放在当前函数的寄存器里。

### 哪些变量必须放在 Frame

PPT 和虎书列出的 frame-resident 原因可以整理成考试表：

| 原因 | 为什么不能只放寄存器 | 考试判断 |
|---|---|---|
| passed by reference | 需要把变量地址传给被调用者 | 需要 frame |
| address taken，例如 C 的 `&x` | 必须有稳定内存地址 | 需要 frame |
| 被 nested procedure 访问 | 内层函数通过 static link 访问外层 frame | 需要 frame |
| 值太大，单个寄存器放不下 | 例如大结构体 | 通常需要内存 |
| array variable | 下标访问需要 base address + offset | 通常需要 frame/内存 |
| 寄存器要用于特定目的 | 例如参数传递寄存器被占用 | 可能暂存到 frame |
| locals/temps 太多 | register allocation spill | spill 到 frame |

历年卷常问“哪种变量需要存在栈帧里”。若选项有 `address taken`，它通常是最稳的正确项。注意“值被传给其他函数”不一定需要 frame；call-by-value 只传值。只有取地址、按引用传递、被内层函数访问等情况才 escape。

call-by-reference 参数的细节：形式参数本质上代表 caller 传来的对象地址。返回这个对象的地址通常不会指向 callee 自己的局部 frame，因此不因为 callee 返回而立刻 dangling；但如果 caller 的对象之后生命周期也结束，仍可能悬空。考试判断要看题目是否限定对象生命周期。

## Block Structure 的三种实现

Tiger 允许 nested function，所以内层函数可能访问外层函数的变量。局部变量可以用 `FP + offset` 访问，但非局部变量必须先找到词法外层的 frame。

PPT 给出三种实现：

| 方法 | 思路 | 优点 | 缺点 |
|---|---|---|---|
| static link | 每个 frame 放一个指向词法父函数最新 frame 的指针 | 每次调用只多传一个指针 | 访问外层变量要沿链走，`O(n)` |
| display | 全局数组 `display[i]` 指向深度 `i` 的最新 frame | 访问任意词法层级 `O(1)` | 进入/退出函数要保存恢复 display，全局状态复杂 |
| lambda lifting | 把被用到的非局部变量改成额外参数 | 运行时不需要 static link/display | 参数变多，不适合所有 higher-order 场景 |

本章考试重点是 static link。display 和 lambda lifting 通常理解优缺点和基本改写即可。

### Dynamic Link

dynamic link 指向调用者的栈帧，用于函数返回时恢复调用链。

### Static Link

static link 指向词法上外层函数的栈帧，用于访问非局部变量。

例：

```text
function outer() =
  var x := 1
  function inner() = x + 1
```

`inner` 访问 `x` 时，不能沿调用者链乱找，而要沿词法嵌套链找到 `outer` 的栈帧。

```text
inner frame --static link--> outer frame
```

static link 可能跳过若干 dynamic frames。它永远指向词法父函数最近一次活跃的 frame，而不是“谁调用我”。

### Static Link 与 Dynamic Link 对比

| 项目 | static link | dynamic link |
|---|---|---|
| 又叫 | access link | control link |
| 指向 | 词法外层过程的 frame | 运行时调用者的 frame |
| 决定因素 | 源代码嵌套结构 | 实际调用序列 |
| 主要用途 | 访问 nonlocal variables | 返回时恢复调用链/旧 FP |
| 传递方式 | 作为隐藏参数显式传给 callee | 常由 prologue 保存旧 FP 形成 |

## Frame 抽象

教材中常把机器相关的栈帧细节封装在 `Frame` 模块中：

| 抽象 | 含义 |
|---|---|
| `F_frame` | 一个函数的栈帧描述 |
| `F_access` | 一个变量如何访问 |
| `InFrame(k)` | 变量在 frame 中，偏移为 `k` |
| `InReg(t)` | 变量在临时寄存器 `t` 中 |
| `F_newFrame` | 创建新函数 frame |
| `F_allocLocal` | 分配局部变量位置 |

`F_access` 是抽象类型：机器无关部分只知道变量是 `InFrame(k)` 或 `InReg(t)`，不直接依赖某个真实机器的布局。这样语义分析不用知道 x86、MIPS 或 SPARC 的具体 frame 格式。

### Level、Access、Formals

Tiger 编译器常再加一层 `Level`，表示词法层级：

| 抽象 | 含义 |
|---|---|
| `Level` | 一个函数的词法层级，内部包含 frame 和 parent level |
| `Access` | 变量访问方式，包含变量所在 level 和 frame access |
| `Formals` | 函数形参访问列表 |

虎书这里有两层抽象：

| 层 | 负责什么 |
|---|---|
| `Frame` | 机器相关的 frame、寄存器、真实偏移 |
| `Translate` | Tiger 词法层级、static link、非局部变量访问 |

`Semant` 在处理函数声明时创建新的 `Tr_level`；在处理变量声明时调用 `Tr_allocLocal(level, escape)`。所以第 08 章的 `VEnv` 后续会从只存类型，扩展为同时存 `Tr_access`。

每个非顶层函数通常有一个隐藏形参：static link。它不是源程序里写出的参数，但会放进 frame 的 formals 中。比如：

```text
function outer(a:int) =
  function inner(b:int) = a + b
```

`inner` 的真实调用参数可理解为：

```text
inner(static_link_to_outer, b)
```

虎书实现常把 static link 当作额外第一个 formal，并且它一定 escape，因为函数体需要从 frame 中取到它去访问外层变量。

### 调用时如何传 static link

调用函数 `f` 时，编译器知道：

- 当前函数所在 level：`currentLevel`
- 被调用函数声明所在 level：`calleeLevel`
- `calleeLevel.parent` 是它词法外层函数的 level

要传给 `f` 的 static link 必须指向 `calleeLevel.parent` 对应的运行时 frame。

算法：

```text
target = calleeLevel.parent
sl = current frame pointer
while currentLevel != target:
  sl = MEM(sl + static_link_offset)
  currentLevel = currentLevel.parent
把 sl 作为隐藏第一个参数传给 callee
```

如果调用的是当前函数直接内层定义的函数，`target == currentLevel`，static link 就是当前 FP。

PPT 的嵌套深度公式更适合手算：

| 调用情况 | static link 应该指向 |
|---|---|
| 调用直接内层函数，`np < nx` 且通常 `nx = np + 1` | 当前 caller 的 frame pointer |
| 调用同层或外层可见函数，`np >= nx` | 从 caller 沿 static link 走 `np - nx + 1` 次，到达 callee 的词法父 frame |

其中 `np` 是 caller 的 nesting depth，`nx` 是 callee 的 nesting depth。`np - nx + 1` 可以编译期算出。

例：`indent` 在 depth 4 调用 `write`，`write` 在 depth 3，二者共同词法外层是 `prettyprint` depth 2。需要沿 `4 - 3 + 1 = 2` 条 static link，从 `indent` 到 `show`，再到 `prettyprint`，把 `prettyprint` 的 frame 作为 `write` 的 static link。

### 非局部变量地址计算

访问变量 `x`：

```text
x.level = 声明 x 的函数 level
currentLevel = 当前函数 level
fp = current FP
while currentLevel != x.level:
  fp = MEM(fp + static_link_offset)
  currentLevel = currentLevel.parent
address = fp + x.offset
```

如果 `x` 在当前 frame，循环 0 次；如果在外两层，沿 static link 走两次。

访问非局部变量的公式更简单：

```text
当前过程深度 np，变量声明所在深度 na
沿 static link 走 np - na 次
再用变量在声明 frame 中的 offset 访问
```

例如在 level4 中访问 level2 的 `a`，走 `4 - 2 = 2` 次。

## View Shift、Prologue/Epilogue

`view shift` 指函数入口处把调用约定中的参数位置搬到函数体统一使用的位置。例如参数刚进入时在寄存器 `r1/r2`，但逃逸参数需要存入 frame：

```text
MOVE(MEM(FP + a_offset), TEMP arg_reg_1)
```

`prologue` 是函数入口代码，常做：

- 保存返回地址和 callee-save 寄存器。
- 建立新栈帧，调整 SP/FP。
- 执行 view shift。

`epilogue` 是函数出口代码，常做：

- 把返回值放入 return-value register。
- 恢复 callee-save 寄存器。
- 销毁栈帧并跳回返回地址。

教材中 `procEntryExit1/2/3` 常分阶段插入这些内容：先在 IR 层处理 view shift，再在汇编层补 sink/live-out 信息，最后生成真实入口出口汇编。

### View Shift 为什么存在

同一个参数在 caller 看来和 callee 看来可能位置不同：

| 视角 | 例子 |
|---|---|
| caller 传参位置 | 第一个参数放 `r1`，多余参数放 outgoing argument area |
| callee 函数体访问位置 | 不逃逸参数可能是 `InReg(t)`，逃逸参数可能是 `InFrame(k)` |

view shift 就是在函数入口把 calling convention 的位置转换成函数体统一使用的位置。后续寄存器分配可能删掉冗余 move。

## Display 与 Lambda Lifting 速记

display 是一个按词法深度索引的 frame pointer 数组：

```text
display[1] -> 最近的 main frame
display[2] -> 最近的 level2 frame
display[3] -> 最近的 level3 frame
```

进入深度 `i` 的函数时，保存旧 `display[i]`，再令 `display[i] = current frame`；退出时恢复旧值。访问深度 `i` 的非局部变量时，直接取 `display[i] + offset`。

lambda lifting 把非局部变量变成显式参数：

```text
原来:
  function level4(z) = z + b + a + global

改写后:
  function level4(z, b, a, global) = z + b + a + global
```

这样所有变量都变成局部变量或参数，但调用处要传更多参数。

## 例题：判断变量位置

```text
function f(a:int) =
  let
    var x := 1
    function g() = x + a
    var y := 2
  in
    g() + y
  end
```

分析：

- `a` 被内层 `g` 引用，逃逸，应在 frame 中。
- `x` 被内层 `g` 引用，逃逸，应在 frame 中。
- `y` 未逃逸，可能放寄存器。
- `g` 调用时需要 static link 指向 `f` 的 frame。

## 常见误区

- static link 不是返回地址。
- dynamic link 反映调用关系，static link 反映词法嵌套关系。
- 局部变量不一定在栈上，可能在寄存器中。
- call-by-value 传值本身不等于 escape；call-by-reference 或 address taken 才需要地址。
- FP/SP 是运行时寄存器，`F_frame` 是编译期描述。
- `Frame` 不应该知道 Tiger 的 static link 语义，static link 由 `Translate` 层处理。
- display 访问外层变量快，但入口/出口维护成本更高。
- 调用约定会影响后面的寄存器分配和指令生成。

## 本章覆盖核对

| PPT/教材点 | 笔记位置 | 考试掌握标准 |
|---|---|---|
| run-time environment | 运行时内存区域 | 能区分 code/static/stack/heap |
| activation record/stack frame | 栈帧里有什么 | 知道每次调用一份 frame |
| globals 和 heap | 运行时内存区域 | 知道 global 固定地址，Tiger record/array 在 heap |
| FP/SP | FP 与 SP | 能解释 FP 稳定、SP 变化、offset 编译期确定 |
| calling convention | 调用约定 | 能说参数、返回值、寄存器保存由约定决定 |
| caller-save/callee-save | Caller-save 与 Callee-save | 能判断谁保存、何时保存 |
| frame-resident variables | 哪些变量必须放在 Frame | 能选 address taken、nested use、reference 等 |
| escape analysis | Escape 分析 | 能按词法深度标记 escape |
| block structure | Block Structure 的三种实现 | 知道 nested functions 访问外层变量的问题 |
| static link | Static Link、调用时如何传 static link | 能画链并算走几次 |
| dynamic link | Static Link 与 Dynamic Link 对比 | 能区分调用者链和词法外层链 |
| display | Display 与 Lambda Lifting 速记 | 理解 `display[i]` 和维护成本 |
| lambda lifting | Display 与 Lambda Lifting 速记 | 能看懂把非局部变量变额外参数 |
| Tiger Frame/Translate | Frame 抽象、Level/Access/Formals | 知道 `Frame` 机器相关，`Translate` 处理 level/static link |
| view shift/prologue/epilogue | View Shift、Prologue/Epilogue | 能解释参数搬移、入口和出口代码 |

## 练习

1. 画出三层嵌套函数调用时的 static link 链。
2. 判断一组变量是否 escape。
3. 给一个函数调用序列，标出 caller-save 和 callee-save 应保存的位置。
4. 解释为什么访问外层变量不能只靠 dynamic link。

## 练习参考答案

见 [23_练习参考答案.md](23_练习参考答案.md) 中对应章节。

## 术语中英对照

| English | 中文 | 考试提示 |
|---|---|---|
| activation record | 活动记录 | 一次调用的运行时记录 |
| stack frame | 栈帧 | activation record 的常用说法 |
| frame pointer, FP | 帧指针 | 稳定基址 |
| stack pointer, SP | 栈指针 | 当前栈顶 |
| calling convention | 调用约定 | 参数、返回、寄存器保存规则 |
| return address | 返回地址 | 调用结束跳回位置 |
| caller-save register | 调用者保存寄存器 | caller 负责保存 |
| callee-save register | 被调用者保存寄存器 | callee 负责保存 |
| leaf procedure | 叶子过程 | 不调用其他函数的过程 |
| escape analysis | 逃逸分析 | 判断变量是否必须放内存 |
| frame-resident variable | frame 中变量 | 存在栈帧 |
| spill | 溢出 | 寄存器不够时存到 frame |
| call-by-value | 按值传递 | 传实参值 |
| call-by-reference | 按引用传递 | 传实参地址/引用 |
| lexical level | 词法层级 | 函数嵌套深度 |
| block structure | 块结构 | 允许嵌套函数/块 |
| nonlocal variable | 非局部变量 | 外层函数中声明的变量 |
| static link | 静态链 | 指向词法外层 frame |
| access link | 访问链 | static link 的别名 |
| dynamic link | 动态链 | 指向调用者 frame |
| control link | 控制链 | dynamic link 的别名 |
| hidden static link parameter | 隐藏静态链参数 | 编译器自动加的形参 |
| formal parameter | 形式参数 | 函数声明中的参数 |
| actual parameter | 实际参数 | 调用时传入的参数 |
| view shift | 视图转换 | 参数从调用约定位置搬到访问位置 |
| prologue | 入口代码 | 建立栈帧 |
| epilogue | 出口代码 | 恢复并返回 |
| return-value register | 返回值寄存器 | 保存函数返回值 |
| word size | 字长 | 一个机器字节数 |
| display | display 表 | 快速访问外层 frame |
| lambda lifting | Lambda 提升 | 把非局部变量改成额外参数 |
| temporary | 临时变量 | IR/汇编中的虚拟寄存器 |
