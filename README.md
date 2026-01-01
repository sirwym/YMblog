# 🚀 YM Blog

> 一个专注于 C++、算法分享与创意游戏展示的现代化 Web 平台。

![Django](https://img.shields.io/badge/Django-5.2-092E20?style=flat-square&logo=django)
![HTMX](https://img.shields.io/badge/HTMX-2.0.7-3D72D7?style=flat-square&logo=htmx)
![Alpine.js](https://img.shields.io/badge/Alpine.js-3.13-8BC0D0?style=flat-square&logo=alpinedotjs)
![Tailwind CSS](https://img.shields.io/badge/Tailwind-4.1-38B2AC?style=flat-square&logo=tailwindcss)
![DaisyUI](https://img.shields.io/badge/DaisyUI-5.5-5A0EF8?style=flat-square)

## 📖 项目概览

**YM Blog** 是一个采用 **前后端不分离** 模式开发的个人技术平台。

项目摒弃了繁重的 SPA 框架，回归 Web 开发本源：以 **Django 模板** 负责服务端渲染 (SSR)，结合 **HTMX** 实现高效的局部刷新，并通过 **Alpine.js** 处理轻量级前端交互。

这种 **HATEOAS** (Hypermedia As The Engine Of Application State) 架构在保持极低开发复杂度和运维成本的同时，实现了优秀的 SEO 友好性、首屏加载速度以及接近单页应用的流畅体验。

---

## 🛠️ 技术栈

| 模块 | 技术选型 | 说明 |
| :--- | :--- | :--- |
| **后端框架** | Django 5.2 | 核心业务逻辑、ORM、模板渲染 |
| **交互引擎** | HTMX 2.0.7 | 处理 AJAX 请求、无限滚动、局部 DOM 替换 |
| **前端逻辑** | Alpine.js 3.13 | 处理 Modal、Dropdown、全屏切换等纯前端状态 |
| **UI 框架** | Tailwind CSS 4.1 | 原子化 CSS，配合 DaisyUI 5.5 组件库 |
| **数据库** | MySQL 8.0 | 生产环境存储 (utf8mb4 字符集) |
| **部署** | Nginx + Gunicorn | 经典的生产环境部署方案 |

---

## ✨ 核心功能模块

### 1. 🏗 系统架构与基础设施
* **环境隔离**: 使用 `django-environ` 管理环境变量，严格区分开发与生产配置。
* **动态配置**: 集成 `django-constance`，支持在后台实时修改网站标题、SEO 关键词、ICP 备案号等，**无需重启服务**。
* **现代化后台**: 基于 **Django Unfold** 主题深度定制，提供美观、高效的 Markdown 编辑体验。
* **性能优化**: 
    * 全库 `utf8mb4` 支持 Emoji。
    * 关键视图通过 `select_related` & `prefetch_related` 彻底解决 N+1 查询问题。
* **安全加固**: 启用 HSTS、Secure Cookies、XSS 防护，全站 HTTPS 适配。

### 2. 📝 博客模块 (Blog)
* **沉浸式阅读**: 支持标准 Markdown、KaTeX 公式渲染、多语言代码高亮。
* **智能目录**: 自动生成 TOC 目录，支持 Sticky 吸顶，长文阅读无压力。
* **高并发计数**: 使用 Django `F()` 表达式实现原子阅读计数，结合 Session 防止防刷新。
* **内容保护**: 支持单篇文章设置访问密码。
* **无限滚动**: 列表页基于 HTMX 实现 `Load More` (outerHTML 替换)，体验丝滑。

### 3. 🎮 游戏工坊 (Game)
* **在线试玩**: 无缝集成 HTML5 / TurboWarp 游戏，站内直接运行。
* **全屏体验**: 基于 Alpine.js (`x-data`) 控制 iframe 全屏切换，无侵入式交互。
* **游客互动**: 
    * 基于 Session 的轻量级点赞系统，无需登录。
    * 前端结合 HTMX 实现无刷新 Toggle 点赞效果。
* **智能推荐**: 
    * 随机算法推荐热门游戏，列表中自动去重。
    * **数字分页**: DaisyUI 风格的智能省略分页 (1 2 ... 5 6)，翻页自动保留筛选参数。

### 4. 🖼️ 资源管理 (Upload)
* **图床功能**: 自定义图片上传模型，支持后台直传，按日期自动归档。
* **所见即所得**: Admin 后台集成缩略图预览。

---

## 💻 本地开发指南

### 前置要求
* Python 3.10+
* MySQL 8.0+ (或使用 SQLite)
* Redis (用于缓存)

### 快速启动

1.  **克隆仓库**
    ```bash
    git clone [https://github.com/your-username/ym-blog.git](https://github.com/your-username/ym-blog.git)
    cd ym-blog
    ```

2.  **创建并激活虚拟环境**
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # macOS/Linux
    source .venv/bin/activate
    ```

3.  **安装依赖**
    ```bash
    pip install -r requirements.txt
    ```

4.  **配置环境变量**
    复制 `.env.example` 为 `.env` 并填入数据库信息：
    ```ini
    DEBUG=True
    SECRET_KEY=your-secret-key
    DB_NAME=ymblog
    DB_USER=root
    DB_PASSWORD=password
    ```

5.  **迁移与运行**
    ```bash
    python manage.py migrate
    python manage.py createsuperuser
    python manage.py runserver
    ```

---

## 🚀 生产环境部署

推荐使用 Ubuntu + Nginx + Gunicorn + Systemd。

1.  **Web Server**: Nginx 处理静态文件、SSL 卸载、反向代理。
2.  **App Server**: Gunicorn 运行 Django WSGI 应用。
3.  **Process Control**: Systemd 守护进程，确保服务自启与崩溃重启。
4.  **SSL**: 使用 Certbot (Let's Encrypt) 自动配置 HTTPS。

---

## 📅 后续开发计划 (Roadmap)

- [ ] **SEO 增强**: 自动生成 sitemap.xml 和 robots.txt。
- [ ] **搜索功能**: 集成 Haystack + Whoosh 实现全站全文搜索。
- [ ] **PWA 支持**: 添加 Service Worker，支持离线访问与“添加到主屏幕”。
- [ ] **数据大屏**: 在后台集成 Chart.js 显示 PV/UV 趋势图。
- [ ] **API 开放**: 使用 DRF 构建 RESTful API，为移动端开发做准备。

---

## 📄 开源协议

本项目采用 [MIT License](LICENSE) 开源。
