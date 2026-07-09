/* ============================================================
   静态站点的渐进增强脚本（内容已在 HTML 中，JS 仅增强交互）
   - 复制按钮（data-copy）
   - 打开网盘（data-open）
   - 参数表展开/收起（.box .toggle）
   - 移动端侧栏汉堡菜单
   ============================================================ */
(function () {
  'use strict';
  var toastEl, toastTimer;

  function toast(msg) {
    if (!toastEl) toastEl = document.getElementById('toast');
    if (!toastEl) return;
    toastEl.textContent = msg;
    toastEl.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toastEl.classList.remove('show'); }, 1600);
  }

  // 页面 <html lang="..."> 由 build.py 按语言子站生成，据此选择提示文案
  function isZh() {
    return (document.documentElement.lang || '').toLowerCase().indexOf('zh') === 0;
  }

  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(function () { toast(isZh() ? '已复制' : 'Copied'); }, fallback);
    } else { fallback(); }
    function fallback() {
      var ta = document.createElement('textarea');
      ta.value = text;
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand('copy'); toast(isZh() ? '已复制' : 'Copied'); }
      catch (e) { toast(isZh() ? '复制失败，请手动复制' : 'Copy failed, please copy manually'); }
      document.body.removeChild(ta);
    }
  }

  document.addEventListener('click', function (ev) {
    var t = ev.target;
    if (t.matches('[data-copy]')) { copyText(t.getAttribute('data-copy')); return; }
    if (t.matches('[data-open]')) { window.open(t.getAttribute('data-open'), '_blank', 'noopener'); return; }
    if (t.matches('.box .toggle')) {
      var box = t.closest('.box');
      if (box) box.querySelector('.detail').classList.toggle('collapsed');
      return;
    }
    if (t.closest('#menu-btn')) { document.body.classList.toggle('nav-open'); return; }
    if (t.id === 'mask') { document.body.classList.remove('nav-open'); return; }
  });
})();
