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
