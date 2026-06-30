/* ============================================================
   MacroHard 系统下载站 —— 前台渲染逻辑（数据驱动 SPA）
   - 读取 data/images.json
   - 侧栏分类、版本子菜单、镜像卡片全部由数据生成
   - 路由：#<分类id> 或 #<分类id>/<版本id>，#home 为首页
   依赖：assets/js/config.js（PAN_TYPES / PAN_ORDER 等）
   ============================================================ */
(function () {
  'use strict';

  var DATA = null;
  var el = function (id) { return document.getElementById(id); };

  /* ---------- 工具 ---------- */
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  var toastTimer;
  function toast(msg) {
    var t = el('toast');
    t.textContent = msg;
    t.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { t.classList.remove('show'); }, 1600);
  }

  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(function () { toast('已复制'); }, fallback);
    } else { fallback(); }
    function fallback() {
      var ta = document.createElement('textarea');
      ta.value = text;
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand('copy'); toast('已复制'); } catch (e) { toast('复制失败，请手动选择'); }
      document.body.removeChild(ta);
    }
  }

  /* ---------- 路由解析 ---------- */
  function parseRoute() {
    var h = (location.hash || '').replace(/^#\/?/, '');
    if (!h || h === 'home') return { cat: 'home', ver: '' };
    var parts = h.split('/');
    return { cat: parts[0], ver: parts[1] || '' };
  }

  function catById(id) {
    return DATA.categories.filter(function (c) { return c.id === id; })[0] || null;
  }

  /* ---------- 渲染：侧栏 ---------- */
  function renderSide(route) {
    var site = DATA.site || {};
    el('brand').innerHTML = esc(site.brand || 'MacroHard') + '<span class="dot">.</span>';
    var html = '<ul>';
    html += navItem('home', '首页', route.cat === 'home');
    DATA.categories.forEach(function (c) {
      html += navItem(c.id, c.name, route.cat === c.id);
    });
    html += '</ul>';
    el('nav').innerHTML = html;
    el('side-foot').textContent = site.subtitle || '';
  }
  function navItem(id, name, active) {
    return '<li class="' + (active ? 'active' : '') + '">' +
      '<a href="#' + esc(id) + '"><i class="ic"></i>' + esc(name) + '</a></li>';
  }

  /* ---------- 渲染：主区 ---------- */
  function renderMain(route) {
    var site = DATA.site || {};
    var crumb = el('crumb');
    var container = el('container');

    // 首页：展示全部镜像按日期倒序
    if (route.cat === 'home') {
      crumb.innerHTML = '最新镜像 <small>' + esc(site.subtitle || '') + '</small>';
      var all = DATA.images.slice().sort(byDateDesc);
      container.innerHTML = noticeHtml() + submenuHtml(null, route) + cardsHtml(all);
      bindCards();
      return;
    }

    var cat = catById(route.cat);
    if (!cat) {
      crumb.textContent = '未找到栏目';
      container.innerHTML = emptyHtml('该栏目不存在', '请从左侧选择一个系统分类');
      return;
    }

    crumb.innerHTML = esc(cat.name) + ' <small>' + esc(site.subtitle || '') + '</small>';

    // 该分类下的镜像
    var list = DATA.images.filter(function (im) { return im.category === cat.id; });
    if (route.ver) list = list.filter(function (im) { return im.version === route.ver; });
    list.sort(byDateDesc);

    container.innerHTML = noticeHtml() + submenuHtml(cat, route) +
      (list.length ? cardsHtml(list) : emptyHtml('暂无镜像', '该分类下还没有发布镜像'));
    bindCards();
  }

  function byDateDesc(a, b) { return (b.date || '').localeCompare(a.date || ''); }

  function noticeHtml() {
    var n = (DATA.site || {}).notice;
    return n ? '<div class="notice">' + esc(n) + '</div>' : '';
  }

  function submenuHtml(cat, route) {
    if (!cat || !cat.versions || !cat.versions.length) return '';
    var html = '<div class="submenu">';
    html += '<a href="#' + esc(cat.id) + '" class="' + (route.ver ? '' : 'active') + '">全部</a>';
    cat.versions.forEach(function (v) {
      html += '<a href="#' + esc(cat.id) + '/' + esc(v.id) + '" class="' +
        (route.ver === v.id ? 'active' : '') + '">' + esc(v.name) + '</a>';
    });
    html += '</div>';
    return html;
  }

  function emptyHtml(title, sub) {
    return '<div class="empty"><div class="big">📦</div><div style="font-size:16px;color:#444;">' +
      esc(title) + '</div><div style="margin-top:6px;">' + esc(sub) + '</div></div>';
  }

  function cardsHtml(list) {
    return '<div class="cards">' + list.map(cardHtml).join('') + '</div>' +
      '<div class="foot">' + esc((DATA.site || {}).footer || '') + '</div>';
  }

  function cardHtml(im) {
    var tags = '<span class="bit">' + esc(im.arch || '') + '</span>';
    if (im.lang) tags += '<span class="lang">' + esc(im.lang) + '</span>';
    if (im.date) tags += '<span class="date">' + esc(im.date) + '</span>';
    (im.editions || []).forEach(function (e) { tags += '<span>' + esc(e) + '</span>'; });

    var params = '';
    (window.PARAM_FIELDS || []).forEach(function (k) {
      var v = (im.params || {})[k];
      if (v) params += '<tr><td class="param-name">' + esc(k) + '</td><td class="param-value">' + esc(v) + '</td></tr>';
    });

    return '<div class="box" data-id="' + esc(im.id) + '">' +
      '<div class="name"><h1>' + esc(im.title) + '</h1>' +
      '<span class="toggle">[ 展开/收起 ]</span></div>' +
      '<div class="tag">' + tags + '</div>' +
      '<div class="detail">' +
      (params ? '<table class="param"><tbody>' + params + '</tbody></table>' : '') +
      '<div class="download">' + linksHtml(im.links || []) + '</div>' +
      '</div></div>';
  }

  function linksHtml(links) {
    var rows = '';
    links.forEach(function (lk) {
      var t = window.panType(lk.type);
      var color = t.color;
      var urlItem =
        '<div class="dl-item">' +
        '<div class="dl-label" style="background:' + color + '">' + esc(t.name) + '</div>' +
        '<input class="dl-input" readonly value="' + esc(lk.url) + '">' +
        '<button class="dl-copy" data-copy="' + esc(lk.url) + '">复制链接</button>' +
        '<button class="dl-open" data-open="' + esc(lk.url) + '">打开</button>' +
        '</div>';
      var passItem = lk.password ?
        '<div class="dl-item pass">' +
        '<div class="dl-label" style="background:' + color + '">提取码</div>' +
        '<input class="dl-input" readonly value="' + esc(lk.password) + '">' +
        '<button class="dl-copy" data-copy="' + esc(lk.password) + '">复制</button>' +
        '</div>' : '';
      rows += '<div class="dl-row">' + urlItem + passItem + '</div>';
    });
    return rows || '<div style="color:#999;font-size:13px;">暂未提供下载链接</div>';
  }

  function bindCards() {
    // 复制
    Array.prototype.forEach.call(document.querySelectorAll('[data-copy]'), function (btn) {
      btn.addEventListener('click', function () { copyText(btn.getAttribute('data-copy')); });
    });
    // 打开网盘
    Array.prototype.forEach.call(document.querySelectorAll('[data-open]'), function (btn) {
      btn.addEventListener('click', function () { window.open(btn.getAttribute('data-open'), '_blank'); });
    });
    // 展开/收起参数表
    Array.prototype.forEach.call(document.querySelectorAll('.box .toggle'), function (tg) {
      tg.addEventListener('click', function () {
        tg.closest('.box').querySelector('.detail').classList.toggle('collapsed');
      });
    });
  }

  /* ---------- 移动端侧栏 ---------- */
  function bindShell() {
    el('menu-btn').addEventListener('click', function () { document.body.classList.toggle('nav-open'); });
    el('mask').addEventListener('click', function () { document.body.classList.remove('nav-open'); });
    document.title = (DATA.site && DATA.site.title) || 'MacroHard 系统下载';
    el('page-title').textContent = document.title;
  }

  /* ---------- 路由调度 ---------- */
  function route() {
    var r = parseRoute();
    renderSide(r);
    renderMain(r);
    document.body.classList.remove('nav-open');
    window.scrollTo(0, 0);
  }

  /* ---------- 启动 ---------- */
  function start() {
    fetch('data/images.json?_=' + Date.now())
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then(function (json) {
        DATA = json;
        DATA.categories = DATA.categories || [];
        DATA.images = DATA.images || [];
        bindShell();
        window.addEventListener('hashchange', route);
        route();
      })
      .catch(function (e) {
        el('container').innerHTML =
          '<div class="empty"><div class="big">⚠️</div><div style="font-size:16px;color:#444;">数据加载失败</div>' +
          '<div style="margin-top:6px;">无法读取 data/images.json（' + esc(e.message) + '）</div></div>';
      });
  }

  document.addEventListener('DOMContentLoaded', start);
})();
