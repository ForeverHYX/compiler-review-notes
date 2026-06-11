# 编译原理复习笔记进度记录

## 2026-06-11

- 恢复长期目标后检查仓库根目录，确认已有 `00` 到 `24` 章复习笔记、`materials/` 课件和虎书 PDF。
- 发现长期计划文件缺失，创建 `task_plan.md`、`findings.md`、`progress.md`。
- 发现目前没有本地浏览器阅读器实现；这是后续最优先的明确交付物。
- 发现 `materials/README.md` 未列出已存在的 `ch18 循环优化.pdf`。
- 发现 `02_词法分析_RE_NFA_DFA_Lex.md` 有未提交改动，后续编辑该文件前需保护现有状态。
- 用户新增要求：稳定更新要及时同步到 GitHub，也可以部署在线阅读器到 `root@116.62.147.239`。
- 选择阅读器实现方向：Python 标准库 HTTP 服务 + 简化 Markdown 渲染 + 从 `23_练习参考答案.md` 自动拆分答案并就地展开。
- 为阅读器新增 `tests/test_reader_server.py`，先看到缺失 `reader_server` 的失败，再实现 `reader_server.py`。
- 阅读器测试首次失败暴露测试假设错误：`23_练习参考答案.md` 也属于“所有笔记”，不应从导航中排除；已修正测试。
- 使用 PyPDF2 抽取本地 `ch2 词法分析.pdf` 和虎书目录，确认第 02 章覆盖依据。
- 参考 Flex 官方手册、Crafting Interpreters scanning 章节、chibicc tokenizer，对 `02_词法分析_RE_NFA_DFA_Lex.md` 做初学者补强：新增阅读路线、token record、手动扫描表、RE 能力边界、DFA 整串识别 vs lexer 前缀切分、Lex 生成器工作流、关键字实现方式、错误处理和覆盖核对。
- 更新 `materials/README.md`，补列 `ch18 循环优化.pdf`。
- 本地阅读器端口验证受沙箱限制：沙箱内客户端连接 `127.0.0.1:8000` 报 `Operation not permitted`；非沙箱 curl/kill 请求被审批服务 503 拒绝。已确认 PID 89651 在端口 8000 监听，但无法在本轮自动 HTTP 抓取页面。
- 增加 `.gitignore` 忽略 Python `__pycache__` 和 `.pyc`，避免测试运行产物进入提交。
- 更新 `README.md`，加入本地阅读器启动命令、访问地址和答案展开说明。
- 已提交并推送第一批更新到 GitHub：`8fa74bc Add browser reader and deepen lexical notes`。
- 服务器检查结果：`root@116.62.147.239` 有 Python/Git/systemd/nginx；现有 `127.0.0.1:8000` 被主页 API gunicorn 占用，不能作为阅读器端口。
- 为服务器部署新增阅读器 `--base-path` 支持，目标是在现有域名下以 `/compiler-notes/` 子路径代理到阅读器服务。
- 服务器无法无凭据从 GitHub HTTPS clone 私有仓库；改用本机 `git archive` 打包当前提交，通过 scp 上传到 `/tmp` 并解压到 `/opt/compiler-review-notes`。
- 服务器 `/opt/compiler-review-notes` 已运行 `python3 -m unittest tests/test_reader_server.py`，8 个测试通过。
- 部署 systemd 服务 `compiler-review-notes.service`，运行命令为 `/usr/bin/python3 /opt/compiler-review-notes/reader_server.py --host 127.0.0.1 --port 8010 --base-path /compiler-notes`，服务已 enabled 且 active。
- nginx 已加入 `/etc/nginx/snippets/compiler-review-notes-location.conf` 并在 `foreverhyx.conf` 的 HTTPS server 中 include，reload 成功。
- 服务器侧验证通过：`https://foreverhyx.top/compiler-notes/` 返回笔记首页，`/compiler-notes/note/02_...md` 返回第 02 章，并包含 `data-answer-key="chapter-02"` 的答案展开控件。
- 本机仍有早先测试启动的 `python3 reader_server.py` 在 `127.0.0.1:8000` 监听；沙箱普通 kill 失败，非沙箱 kill 审批服务 503，未继续绕路。
- 用户明确调整方向：不需要面面俱到的小教材式扩写，目标是面向考试复习，核心是覆盖 PPT 知识点、能处理历年卷判断/单选/大题。
- 检查 `24_回忆卷解析与考点加固.md`，已发现用户新贴的判断题、选择题和大题大多已整理进去；后续用这些题校准各章节应讲到的深度和题型训练。
- 用户进一步澄清：笔记顺序仍按教材/PPT 章节讲知识点，不改成题库或考点乱序；历年卷只用于控制每章深度和取舍。
- 补强 `03_语法分析_CFG_推导_二义性.md`：新增本章边界、token 视角、straight-line program 文法、EOF marker、LL/LR 推导视角、句型/句子/语言、parse tree 与推导关系、parsing 搜索视角、优先级/结合性、dangling else、正则语言 vs CFG、PPT 覆盖核对。
- 本轮恢复后再次确认用户要求：顺序按教材/PPT，知识点可适度合并，但不做零散题库化；只专注考试和 PPT 范围，不额外拓展。
- 抽取 `materials/ch3 语法分析-2(TD).pdf` 第 81-115 页，确认后半部分覆盖表驱动示例、递归下降实现、文法改造和错误恢复；第一次 PDF 抽取命令因 `python3 -c` 换行转义失败，已改用脚本式命令成功抽取，并记录该错误。
- 补强 `04_LL1_自顶向下分析.md`：新增本章边界、回溯示例、递归下降何时需要 FIRST/FOLLOW、FIRST 右部串说明、FOLLOW 不含 epsilon、空表项/冲突表项、LL(1) 快速排除性质、表驱动压栈顺序、提左公因子目的、错误恢复策略对比和 PPT 覆盖核对。
- 更新 `task_plan.md` 和 `findings.md`，记录第 04 章补强依据和当前继续按章节顺序推进的约束。
- 本地验证通过：`python3 -m unittest tests/test_reader_server.py` 8 个测试通过，Markdown 表格结构检查通过，`git diff --check` 无输出。
- 已提交并推送第 04 章补强：`d206198 Deepen LL1 notes for exam scope`。
- 已部署 `d206198` 到服务器；服务器端阅读器测试 8 个通过，`compiler-review-notes.service` 为 active，公网第 04 章页面已验证包含“本章只学到哪里”“本章覆盖核对”等新增内容。

## 2026-06-12

- 恢复长期计划，确认当前方向仍是按教材/PPT章节顺序推进，下一章为 LR(0)/SLR 自底向上分析。
- 抽取 `materials/ch3 语法分析-3(BU)-LR(0)SLR(1).pdf` 全部 98 页摘要，确认 PPT 主线包括 shift-reduce 分界点模型、最右推导逆过程、LR(0) item/NFA/DFA、closure/goto、ACTION/GOTO、状态栈算法、LR(0) 局限、SLR 用 FOLLOW 限制 reduce。
- 抽取虎书 LR parsing 对应页，确认状态栈算法、增广文法、`$`/accept、LR(0) 与 SLR 填表规则的教材表述。
- 补强 `05_LR0_SLR_自底向上分析.md`：新增本章边界、shift-reduce 分界点、handle/viable prefix、LR(0) 中 `0` 的含义、LR(0) NFA 到 DFA 直觉、EOF/accept 边界、ACTION/GOTO 填表检查清单、epsilon 规约栈规则、SLR 流程与局限、PPT 覆盖核对。
- 更新 `task_plan.md` 和 `findings.md`，记录第 05 章已按 PPT/考试范围补强，下一步转向第 06 章 LR(1)/LALR/Yacc。
- 本地验证通过：`python3 -m unittest tests/test_reader_server.py` 8 个测试通过，Markdown 表格结构检查通过，`git diff --check` 无输出。
- 已提交并推送第 05 章补强：`a9b43e2 Deepen LR0 SLR notes for exam scope`。
- 已部署 `a9b43e2` 到服务器；服务器端阅读器测试 8 个通过，`compiler-review-notes.service` 为 active，公网第 05 章页面已验证包含“本章只学到哪里”“Handle 与 Viable Prefix”“本章覆盖核对”等新增内容。
- 继续推进第 06 章 LR(1)/LALR/Yacc：抽取 `materials/ch3 语法分析-4(LR(1), LALR(1), etc).pdf` 全部 62 页摘要，并抽取虎书 parser generator 对应页，确认 PPT/教材主线包括 LR(1) closure/goto/reduce、LALR 合并、Yacc 三段式、冲突规则、优先级、`error` token 和错误恢复。
- 补强 `06_LR1_LALR_Yacc.md`：新增本章边界、SLR FOLLOW 近似局限、LR(1) 起始 lookahead/compact 表示、`FIRST(beta a)` 手算提示、LR(1) 填表规则、LALR 合并边和状态、LR 系列方法对比、Yacc 三段式、语义动作执行时机、默认冲突规则、`%prec/%nonassoc`、`error` token 恢复步骤、语法分析方法总览和 PPT 覆盖核对。
- 更新 `task_plan.md` 和 `findings.md`，记录第 06 章已按 PPT/考试范围补强，下一步转向第 07 章 AST 抽象语法。
- 本地验证通过：`python3 -m unittest tests/test_reader_server.py` 8 个测试通过，Markdown 表格结构检查通过，`git diff --check` 无输出。
- 已提交并推送第 06 章补强：`3cf16a1 Deepen LR1 LALR Yacc notes for exam scope`。
- 已部署 `3cf16a1` 到服务器；服务器端阅读器测试 8 个通过，`compiler-review-notes.service` 为 active，公网第 06 章页面已验证包含“本章只学到哪里”“SLR 为什么还不够精确”“语法分析方法总览”“本章覆盖核对”等新增内容。
- 继续推进第 07 章 AST 抽象语法：抽取 `materials/ch4 抽象语法.pdf` 全部 48 页摘要，并抽取虎书 Abstract Syntax 对应页，确认 PPT/教材主线包括属性文法思想、semantic action、语义值栈、parse tree vs AST、AST 表示、AST 构造、position 字段和 Yacc `pos` 技巧。
- 补强 `07_AST_抽象语法.md`：新增本章边界、属性文法考试深度、parse tree 与 AST 的接口意义、为什么不在 parser action 里做完整编译、top-down/bottom-up 构造方式对比、Tiger 连续函数/类型声明合并、`&`/`|`/一元负号的 AST 表示、`S_symbol`/`escape`、position stack/Yacc `pos` 技巧、语义值栈规则和 PPT 覆盖核对。
- 更新 `task_plan.md` 和 `findings.md`，记录第 07 章已按 PPT/考试范围补强，下一步转向第 08 章语义分析、符号表与类型检查。
- 本地验证通过：`python3 -m unittest tests/test_reader_server.py` 8 个测试通过，Markdown 表格结构检查通过，`git diff --check` 无输出。
- 已提交并推送第 07 章补强：`c327bb8 Deepen AST notes for exam scope`。
- 已部署 `c327bb8` 到服务器；服务器端阅读器测试 8 个通过，`compiler-review-notes.service` 为 active，公网第 07 章页面已验证包含“本章只学到哪里”“属性文法只掌握思想”“本章覆盖核对”等新增内容。
- 继续推进第 08 章语义分析、符号表与类型检查：抽取 `materials/ch5 语义分析.pdf` 全部 93 页摘要，并抽取虎书 Semantic Analysis 对应页，确认 PPT/教材主线包括广义/狭义语义分析、符号表实现、Tiger TEnv/VEnv、name equivalence、nil、typing judgment、`transExp/transVar/transDec/transTy` 和递归声明 two-pass。
- 补强 `08_语义分析_符号表_类型检查.md`：新增本章边界、binding 信息类别、多符号表与名字空间、三类命令式符号表实现、external chaining 判断题陷阱、functional persistent environment、string interning、type system 考试四问、Tiger name equivalence 精确解释、形式化记号阅读深度、`transVar` 三类变量访问、`transDec` 声明检查、作用域大题模板和 PPT 覆盖核对。
- 更新 `task_plan.md` 和 `findings.md`，记录第 08 章已按 PPT/考试范围补强，下一步转向第 09 章活动记录、栈帧与变量逃逸。
- 本地验证通过：`python3 -m unittest tests/test_reader_server.py` 8 个测试通过，Markdown 表格结构检查通过，`git diff --check` 无输出。
- 已提交并推送第 08 章补强：`f8521ef Deepen semantic analysis notes for exam scope`。
- 已部署 `f8521ef` 到服务器；服务器端阅读器测试 8 个通过，`compiler-review-notes.service` 为 active。公网 `curl` 第 08 章页面时沙箱 DNS 失败，提权重试被审批服务 503 拒绝，本轮未做公网页面抓取验证。
