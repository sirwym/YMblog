<div align="center">
  <img src="static/img/ym-logo.png" alt="YM Blog Logo" width="120">
  <h1>YM Blog</h1>
</div>

<div align="center">

![Django](https://img.shields.io/badge/Django-5.2-092E20?style=flat-square&logo=django)
![Celery](https://img.shields.io/badge/Celery-5.3-37814A?style=flat-square&logo=celery)
![Go-Judge](https://img.shields.io/badge/Go--Judge-Sandbox-00ADD8?style=flat-square&logo=go)
![HTMX](https://img.shields.io/badge/HTMX-2.0.7-3D72D7?style=flat-square&logo=htmx)
![Alpine.js](https://img.shields.io/badge/Alpine.js-3.13-8BC0D0?style=flat-square&logo=alpinedotjs)
![Tailwind CSS](https://img.shields.io/badge/Tailwind-4.1-38B2AC?style=flat-square&logo=tailwindcss)

</div>

## 📖 项目概览

**YM Blog** 是一个采用 **前后端不分离** 模式开发的现代化个人技术平台，集成了博客、游戏工坊与开发者工具箱。

项目摒弃了繁重的 SPA 框架，回归 Web 开发本源：以 **Django 模板** 负责服务端渲染 (SSR)，结合 **HTMX** 实现高效的局部刷新，并通过 **Alpine.js** 处理轻量级前端交互。后台任务处理采用 **Celery + Redis** 架构，代码评测基于 **Go-Judge** 沙箱。

---

## 🛠️ 技术栈

| 模块 | 技术选型 | 说明 |
| :--- | :--- | :--- |
| **后端框架** | Django 5.2 | 核心业务逻辑、ORM、模板渲染 |
| **异步任务** | Celery + Redis | 处理 AI 生成、耗时评测任务 |
| **代码沙箱** | Go-Judge | 高性能安全沙箱，用于 C++ 编译与运行 |
| **交互引擎** | HTMX 2.0.7 | 处理 AJAX 请求、无限滚动、局部 DOM 替换 |
| **前端逻辑** | Alpine.js 3.13 | 处理 Modal、Dropdown、全屏切换等纯前端状态 |
| **代码编辑** | Monaco Editor | VS Code 同款编辑器，极致性能优化 |
| **数据库** | MySQL 8.0 | 生产环境存储 (utf8mb4 字符集) |
| **部署** | Nginx + Gunicorn | Gzip 深度优化，Systemd 进程守护 |

---

## ✨ 核心功能模块

### 1. 🏗 系统架构与基础设施
* **动态配置**: 集成 `django-constance`，支持后台实时修改 SEO 配置，无需重启。
* **极致性能**: 
    * **Nginx Gzip**: 针对 JS/CSS/JSON/TTF 开启深度压缩，Monaco Editor 加载速度提升 400%。
    * **内存优化**: 针对 2C2G 服务器调优，配置 Gunicorn/Celery 自动重启机制与 Swap 兜底。
    * **ORM 优化**: 关键视图全覆盖 `select_related`，杜绝 N+1 查询。
* **安全加固**: 启用 HSTS、Secure Cookies、XSS 防护，全站 HTTPS 适配。

### 2. 📝 博客模块 (Blog)
* **沉浸阅读**: Markdown/KaTeX 渲染，自动生成 Sticky 目录。
* **原子计数**: `F()` 表达式并发阅读计数，Session 防刷。
* **内容保护**: 单篇文章密码锁功能。
* **HTMX**: 评论区、文章列表无限滚动均采用 HTML 片段替换技术。

### 3. 🛠️ 开发者工具箱 (Tools) 🔥NEW
* **C++ 在线运行器**:
    * 集成 **Monaco Editor**，支持语法高亮、智能提示、O2 优化开关。
    * 后端对接 **Go-Judge**，支持秒级编译运行，提供内存/时间消耗报告。
    * **安全沙箱**: 严格限制 CPU/Memory 配额，防止恶意代码危害服务器。
* **AI 测试数据生成器**:
    * 基于 **DeepSeek** 大模型，根据题面自动编写 `gen.py` (生成器) 和 `val.py` (校验器)。
    * **自动化流水线**: 自动编译标程 -> 并发生成数据 -> 自动校验合法性 -> 打包 ZIP 下载。
    * **Prompt 工程**: 独创 v6.6 提示词策略，强制 O(N) 复杂度生成，防止 OOM 和超时。

### 4. 🎮 游戏工坊 (Game)
* **在线试玩**: 集成 HTML5 / TurboWarp 游戏。
* **无侵入交互**: Alpine.js 控制全屏，HTMX 处理无刷新点赞。

---

## 💻 本地开发指南

### 前置要求
* Python 3.10+
* MySQL 8.0+
* Redis (必须，用于 Celery)
* Go-Judge (必须，用于沙箱服务)

### 快速启动

1.  **克隆与环境**
    ```bash
    git clone [https://github.com/your-username/ym-blog.git](https://github.com/your-username/ym-blog.git)
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **配置环境变量** (`.env`)
    ```ini
    DEBUG=True
    # ... 数据库配置 ...
    GO_JUDGE_BASE_URL=http://localhost:5050
    LLM_API_KEY=sk-xxxx
    ```

3.  **启动服务**
    ```bash
    # 终端 1: Django
    python manage.py runserver
    # 终端 2: Celery
    celery -A config worker -l info --concurrency=1
    # 终端 3: Go-Judge
    ./go-judge -http-addr :5050
    ```

---

## 📅 后续开发计划 (Roadmap)
- [x] **工具箱**: C++ 在线运行、AI 数据生成器 (已上线)
- [ ] **搜索功能**: 集成 Haystack + Whoosh 实现全站全文搜索。
- [ ] **PWA 支持**: 添加 Service Worker，支持离线访问。
- [ ] **API 开放**: 使用 DRF 构建 RESTful API。

---

## 📄 开源协议

本项目采用 [MIT License](LICENSE) 开源。