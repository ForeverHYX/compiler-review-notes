# 09 活动记录、栈帧与 Static Link

## 本章解决什么问题

函数调用不是简单跳转。调用时必须保存返回地址、参数、局部变量、临时值和部分寄存器。活动记录就是一次函数调用在运行时占用的一块栈空间，也叫栈帧。

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

## FP 与 SP

- `SP` 指向当前栈顶，随着 push/pop 或分配局部空间变化。
- `FP` 指向当前栈帧中一个稳定位置，用于访问固定偏移的参数和局部变量。

初学者最容易混淆：运行时地址是动态的，但相对 `FP` 的偏移可以编译期确定。

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

## Static Link 与 Dynamic Link

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

### Level、Access、Formals

Tiger 编译器常再加一层 `Level`，表示词法层级：

| 抽象 | 含义 |
|---|---|
| `Level` | 一个函数的词法层级，内部包含 frame 和 parent level |
| `Access` | 变量访问方式，包含变量所在 level 和 frame access |
| `Formals` | 函数形参访问列表 |

每个非顶层函数通常有一个隐藏形参：static link。它不是源程序里写出的参数，但会放进 frame 的 formals 中。比如：

```text
function outer(a:int) =
  function inner(b:int) = a + b
```

`inner` 的真实调用参数可理解为：

```text
inner(static_link_to_outer, b)
```

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
- FP/SP 是运行时寄存器，`F_frame` 是编译期描述。
- 调用约定会影响后面的寄存器分配和指令生成。

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
| escape analysis | 逃逸分析 | 判断变量是否必须放内存 |
| lexical level | 词法层级 | 函数嵌套深度 |
| nonlocal variable | 非局部变量 | 外层函数中声明的变量 |
| static link | 静态链 | 指向词法外层 frame |
| dynamic link | 动态链 | 指向调用者 frame |
| hidden static link parameter | 隐藏静态链参数 | 编译器自动加的形参 |
| formal parameter | 形式参数 | 函数声明中的参数 |
| actual parameter | 实际参数 | 调用时传入的参数 |
| view shift | 视图转换 | 参数从调用约定位置搬到访问位置 |
| prologue | 入口代码 | 建立栈帧 |
| epilogue | 出口代码 | 恢复并返回 |
| return-value register | 返回值寄存器 | 保存函数返回值 |
| word size | 字长 | 一个机器字节数 |
| display | display 表 | 快速访问外层 frame |
| frame-resident variable | frame 中变量 | 存在栈帧 |
| temporary | 临时变量 | IR/汇编中的虚拟寄存器 |
