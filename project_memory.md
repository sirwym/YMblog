# Project Memory & Context: YM Blog

## 1. 项目身份
* **名称**: YM Blog (个人技术平台)
* **架构模式**: Django Monolith (SSR) + HTMX (局部刷新) + Alpine.js (前端交互)
* **核心理念**: HATEOAS, 去除重型 SPA 框架，追求极致的首屏速度和 SEO。
* **部署环境**: Ubuntu 2C2G 服务器 (资源受限环境)。

## 2. 技术栈详细
* **Backend**: Django 5.2, Celery 5.3 (Async Tasks), Redis (Cache/Broker).
* **Database**: MySQL 8.0 (utf8mb4).
* **Frontend**:
    * **Logic**: Alpine.js v3.13.
    * **AJAX**: HTMX v2.0.7.
    * **Styling**: Tailwind CSS v4.1 + DaisyUI v5.5.
    * **Editor**: Monaco Editor (AMD Load via).
    * **Admin UI**: `django-unfold` (深度定制侧边栏与配色，集成 KaTeX 公式渲染)。
* **Sandbox**: Go-Judge (HTTP API at `:5050`) 用于 C++ 编译运行。
* **Infrastructure**: Nginx (Reverse Proxy + Gzip), Gunicorn (WSGI), Systemd.

## 3. 核心功能模块与实现细节

### A. 开发者工具 (Tools App)
* **权限**: `check_tool_permission` 控制访问，支持工具密码锁 (Session 记录解锁状态)。
* **C++ 运行器 (`cpp_runner`)**:
    * **架构**: 前端 Monaco Editor (O2选项) -> 后端 `judge_utils.py` -> Go-Judge 沙箱。
    * **流程**: 两步走机制，先编译缓存可执行文件，再运行输入数据。
    * **稳定性机制 (Critical)**:
        * **流式处理**: 大于 1MB (`LARGE_FILE_THRESHOLD`) 的测试点强制使用 `client.stream` 下载并落盘，防止内存爆炸。
        * **智能分级**: `pick_scale` 算法根据测试点总数动态分配数据规模 (基础/中等/极限)，20组数据时仅后7组为大规模。
        * **并发控制**: 使用 `asyncio.Semaphore(3)` 严格限制并发评测请求，防止压垮 Go-Judge。
* **AI 测试数据生成器 (`testcase_gen`)**:
    * **AI 引擎**: DeepSeek-Chat。
    * **Prompt 策略**: `ai_utils.py` (v6.6) 包含严格的性能约束（禁止 O(N^2) 查重，禁止 O(N^2) BFS 校验，强制使用 set 和 DSU）。
    * **流程**: `tasks.py` (Celery) 异步生成代码 -> `batch_generate_and_run` 并发调用 Driver 脚本 -> 自动打包 ZIP。

### B. 博客与游戏
* **Blog**: Markdown 渲染，TOC 目录，F() 表达式原子计数。
* **Game**: iframe 嵌入，Session 点赞系统。

### C. 动态配置与运营 (System Config)
* **实现**: `django-constance` (Database Backend) + `django-unfold` 集成。
* **Capability**: 支持后台热更新站点元数据 (Name, SEO, ICP) 及系统级开关 (Maintenance Mode)，无需重新部署。

## 4. 关键配置与约束 (Critical Constraints)

### 服务器限制 (2C 2G)
* **Gunicorn**: 配置为 `workers=2`，且设置 `--max-requests 1000` 防止内存泄漏。
* **Celery**: 配置为 `--concurrency=1`，且设置 `--max-tasks-per-child=1000`，AI 任务极耗内存，必须定期重启。
* **MySQL**: 关闭 `performance_schema`，限制 `innodb_buffer_pool_size=128M`。
* **Swap**: 启用 2GB Swap 防止 OOM。
* **Logging**: 生产级配置。`django` 核心仅记录 WARNING+，业务模块 (`tools`) 记录 INFO。使用 `RotatingFileHandler` (20MB*5) 防止日志占满磁盘。

### 性能优化策略
* **Nginx Gzip**: 
    * 开启类型: `text/css`, `application/json`, `application/javascript`。

### 代码规范
* **Python**: 使用 Type Hints，异步 IO (`httpx`, `asyncio`) 处理外部请求。
* **Prompt Engineering**: 生成代码必须包含 `sys.setrecursionlimit`，且使用流式输出 (`out/flush`) 防止大规模数据导致 OOM。

## 5. 已完成里程碑
* [x] 集成 Go-Judge 实现安全沙箱。
* [x] 完成 AI 辅助出题系统（含 gen/val/sol 自动化流水线）。
* [x] 全站 Nginx Gzip 与 静态资源缓存策略 (30天)。
* [x] 2G 内存环境下的高可用配置 (Systemd/Swap/Logging)。

## 6. 当前任务上下文
(此处留白，每次复制时可补充当前正在解决的问题)