// static/admin/js/admin_katex_config.js

document.addEventListener("DOMContentLoaded", function() {

    // 1. KaTeX 配置
    const katexConfig = {
        delimiters: [
            {left: '$$', right: '$$', display: true},
            {left: '$', right: '$', display: false},
            {left: '\\(', right: '\\)', display: false},
            {left: '\\[', right: '\\]', display: true}
        ],
        ignoredTags: ["script", "noscript", "style", "textarea", "pre", "code"],
        throwOnError: false
    };

    // 2. 封装渲染函数
    const renderMath = function(element) {
        if (typeof renderMathInElement !== 'undefined' && element) {
            try {
                renderMathInElement(element, katexConfig);
            } catch (e) {
                console.error("KaTeX render error:", e);
            }
        }
    };

    // 3. 初始渲染 (针对详情页的 Readonly 字段或已存在的静态内容)
    renderMath(document.body);

    // 4. 定义一个核心监听器
    // 这个观察者会盯着整个页面，一旦发现预览窗口里的内容变了，就立刻渲染
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            // A. 检查是否有新节点被添加 (例如刚点击预览按钮时)
            if (mutation.addedNodes.length > 0) {
                mutation.addedNodes.forEach(node => {
                    if (node.nodeType === 1) { // 确保是元素节点
                        // 检查是否是预览容器 (涵盖全屏和分栏两种模式)
                        if (node.classList.contains('editor-preview') ||
                            node.classList.contains('editor-preview-side')) {
                            renderMath(node);
                        }
                    }
                });
            }

            // B. 检查目标节点本身是否是预览容器 (例如正在打字，内容被替换时)
            // EasyMDE 在更新预览时，通常会修改预览容器的 innerHTML
            const target = mutation.target;
            if (target.nodeType === 1) {
                if (target.classList.contains('editor-preview') ||
                    target.classList.contains('editor-preview-side')) {
                    renderMath(target);
                }
            }
        });
    });

    // 5. 启动全局监听
    // 监听 childList (子节点变化) 和 subtree (所有后代)，确保捕捉到任何动态插入
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
});