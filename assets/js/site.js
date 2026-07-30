/* ============================================================
   静态站点的渐进增强脚本（内容已在 HTML 中，JS 仅增强交互）
   - 复制按钮（data-copy）
   - 打开网盘（data-open）—— 仅在页面配置启用时，对指定网盘改为弹窗二维码；其余网盘正常新开标签页
   - 参数表展开/收起（.box .toggle），移动端默认只展开第一个 box
   - 移动端侧栏汉堡菜单
   ============================================================ */
(function () {
  'use strict';
  var toastEl, toastTimer;
  var qrLastFocus;
  var qrModalPanTypes = (document.body.getAttribute('data-qr-pan-types') || '')
    .split(',')
    .map(function (item) { return item.trim(); })
    .filter(Boolean);

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

  function isMobile() {
    return /Android|iPhone|iPad|iPod|Windows Phone|Mobile|HarmonyOS/i.test(navigator.userAgent);
  }

  function shouldOpenQrModal(pan) {
    return qrModalPanTypes.indexOf(pan) !== -1 && !isMobile();
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

  function closeLangSwitch() {
    var ls = document.getElementById('lang-switch');
    if (!ls || !ls.classList.contains('open')) return;
    ls.classList.remove('open');
    var btn = document.getElementById('lang-switch-btn');
    if (btn) btn.setAttribute('aria-expanded', 'false');
  }

  // 仅对配置中启用的网盘展示二维码弹窗，并根据网盘类型显示对应的 App 提示
  // 二维码在本地生成（assets/js/qrcode.js），不请求任何第三方接口
  function openQrModal(url, pan) {
    var modal = document.getElementById('qr-modal');
    var mask = document.getElementById('qr-mask');
    var wrap = document.getElementById('qr-img-wrap');
    var urlEl = document.getElementById('qr-url');
    var titleEl = document.getElementById('qr-title');
    var hintEl = document.getElementById('qr-hint');
    if (!modal || !mask || !wrap || typeof qrcode === 'undefined') {
      window.open(url, '_blank', 'noopener');
      return;
    }
    var panKey = (pan === 'quark' || pan === 'baidu') ? pan : '';
    var title = modal.getAttribute(panKey ? 'data-qr-' + panKey + '-title' : 'data-qr-title') || '';
    var hint = modal.getAttribute(panKey ? 'data-qr-' + panKey + '-hint' : 'data-qr-hint') || '';
    try {
      var qr = qrcode(0, 'M'); // typeNumber=0 -> 自动选择能容纳数据的最小规格
      qr.addData(url);
      qr.make();
      wrap.innerHTML = qr.createSvgTag({ cellSize: 4, margin: 4, scalable: true });
    } catch (e) {
      wrap.innerHTML = '';
      window.open(url, '_blank', 'noopener');
      return;
    }
    if (titleEl) titleEl.textContent = title;
    if (hintEl) hintEl.textContent = hint;
    modal.setAttribute('aria-label', title || '');
    if (urlEl) urlEl.textContent = url;
    qrLastFocus = document.activeElement;
    mask.classList.add('show');
    modal.classList.add('show');
    modal.setAttribute('aria-hidden', 'false');
    var closeBtn = document.getElementById('qr-close');
    if (closeBtn) closeBtn.focus();
  }

  function closeQrModal() {
    var modal = document.getElementById('qr-modal');
    var mask = document.getElementById('qr-mask');
    if (!modal || !mask || !modal.classList.contains('show')) return;
    mask.classList.remove('show');
    modal.classList.remove('show');
    modal.setAttribute('aria-hidden', 'true');
    if (qrLastFocus && qrLastFocus.focus) qrLastFocus.focus();
  }

  document.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape') closeQrModal();
  });

  // 移动端（窄屏，断点与 style.css 的 @media (max-width: 860px) 一致）
  // 默认只展开第一个 box，其余折叠，减少一屏内的信息量
  (function collapseExtraBoxesOnMobile() {
    if (!window.matchMedia || !window.matchMedia('(max-width: 860px)').matches) return;
    var boxes = document.querySelectorAll('.box');
    for (var i = 1; i < boxes.length; i++) {
      var detail = boxes[i].querySelector('.detail');
      if (detail) detail.classList.add('collapsed');
    }
  })();

  document.addEventListener('click', function (ev) {
    var t = ev.target;
    if (t.matches('[data-copy]')) { copyText(t.getAttribute('data-copy')); return; }
    if (t.matches('[data-open]')) {
      var url = t.getAttribute('data-open');
      var pan = t.getAttribute('data-pan');
      if (shouldOpenQrModal(pan)) {
        ev.preventDefault();
        openQrModal(url, pan);
      } else {
        window.open(url, '_blank', 'noopener');
      }
      return;
    }
    if (t.id === 'qr-close' || t.id === 'qr-mask') { closeQrModal(); return; }
    if (t.matches('.box .toggle')) {
      var box = t.closest('.box');
      if (box) box.querySelector('.detail').classList.toggle('collapsed');
      return;
    }
    if (t.closest('#menu-btn')) { document.body.classList.toggle('nav-open'); return; }
    if (t.id === 'mask') { document.body.classList.remove('nav-open'); return; }
    if (t.closest('#lang-switch-btn')) {
      var ls = document.getElementById('lang-switch');
      if (ls) {
        var open = ls.classList.toggle('open');
        t.closest('#lang-switch-btn').setAttribute('aria-expanded', open ? 'true' : 'false');
      }
      return;
    }
    if (!t.closest('#lang-switch')) { closeLangSwitch(); }
  });
})();
