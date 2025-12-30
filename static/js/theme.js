/**
 * theme.js
 * 处理 DaisyUI 主题切换逻辑
 */
document.addEventListener('DOMContentLoaded', () => {

    // 监听所有带有 data-set-theme 属性的按钮点击事件
    document.addEventListener('click', (e) => {
        const themeBtn = e.target.closest('[data-set-theme]');
        if (themeBtn) {
            const theme = themeBtn.getAttribute('data-set-theme');

            // 1. 设置 HTML 属性
            document.documentElement.setAttribute('data-theme', theme);

            // 2. 保存到本地存储
            localStorage.setItem('theme', theme);

            // 3. 关闭下拉菜单 (通过移除焦点)
            themeBtn.blur();
            const dropdown = themeBtn.closest('.dropdown');
            if(dropdown) {
                dropdown.removeAttribute('open');
                // 强制让它失去焦点，解决某些移动端 Safari 的顽固问题
                dropdown.blur();
            }
        }
    });

});