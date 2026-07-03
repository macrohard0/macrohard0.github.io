#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
静态站点生成器 —— 从 data/images.json 生成对搜索引擎友好的静态 HTML。

用法：
    python build.py

产物（均写到仓库根目录，GitHub Pages 直接托管）：
    index.html                首页
    <cat>.html                分类页（= 该分类最新版本，如 win11.html = 26H1）
    <cat>/<ver>.html          各历史版本页（如 win11/25h2.html）
    sitemap.xml               站点地图
    robots.txt                （补上 Sitemap 行）

设计要点：
    - 内容在服务端就渲染进 HTML（利于收录），导航用真实 <a> 链接
    - 复用现有 assets/css/style.css；复制/展开/移动端菜单交给 assets/js/site.js（渐进增强）
    - 下载链接来自 images.json；外链加 rel="nofollow"
    - 路径按页面深度用相对前缀（本地 file://、localhost、根域名都能跑）
"""
import json, os, html, shutil, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, 'data', 'images.json')
BASE_URL = 'https://macrohard0.github.io'   # 用于 canonical / sitemap 的绝对域名

# 与 assets/js/config.js 的 PAN_TYPES 保持一致（改这里也要改那边）
PAN = {
    'quark':  ('夸克网盘', '#2D5BFF'),
    'baidu':  ('百度网盘', '#06A7FF'),
    'aliyun': ('阿里云盘', '#FF6A00'),
    'tianyi': ('天翼云盘', '#D9001B'),
    'xunlei': ('迅雷网盘', '#1B7BFF'),
    'weiyun': ('腾讯微云', '#00C250'),
    'yidong': ('移动云盘', '#3A8FFF'),
    'pan123': ('123云盘',  '#2A66FF'),
    'other':  ('其他网盘', '#7A7F8C'),
}
def pan(t):
    return PAN.get(t, PAN['other'])

PARAM_FIELDS = ['文件名', 'SHA-256', 'SHA-1', 'MD5', '文件大小']

# 百度统计（沿用你在 index.html 里加的那段）
BAIDU_HM = '54f24ee5c82c27e994fb615aa3173346'


def e(s):
    return html.escape('' if s is None else str(s), quote=True)


# ---------------------------------------------------------------- 片段渲染
def render_tags(im):
    out = '<span class="bit">%s</span>' % e(im.get('arch', ''))
    if im.get('lang'):
        out += '<span class="lang">%s</span>' % e(im['lang'])
    if im.get('date'):
        out += '<span class="date">%s</span>' % e(im['date'])
    for ed in im.get('editions', []):
        out += '<span>%s</span>' % e(ed)
    return out


def render_params(im):
    rows = ''
    p = im.get('params', {}) or {}
    for k in PARAM_FIELDS:
        v = p.get(k)
        if v:
            rows += '<tr><td class="param-name">%s</td><td class="param-value">%s</td></tr>' % (e(k), e(v))
    if not rows:
        return ''
    return '<table class="param"><tbody>%s</tbody></table>' % rows


def render_links(links):
    if not links:
        return '<div style="color:#999;font-size:13px;">暂未提供下载链接，即将更新</div>'
    out = ''
    for lk in links:
        name, color = pan(lk.get('type'))
        url = lk.get('url', '')
        if not url:
            continue
        pwd = lk.get('password', '')
        url_item = (
            '<div class="dl-item">'
            '<div class="dl-label" style="background:%s">%s</div>'
            '<input class="dl-input" readonly value="%s">'
            '<button class="dl-copy" data-copy="%s">复制链接</button>'
            '<button class="dl-open" data-open="%s">打开</button>'
            '</div>' % (color, e(name), e(url), e(url), e(url))
        )
        pass_item = ''
        if pwd:
            pass_item = (
                '<div class="dl-item pass">'
                '<div class="dl-label" style="background:%s">提取码</div>'
                '<input class="dl-input" readonly value="%s">'
                '<button class="dl-copy" data-copy="%s">复制</button>'
                '</div>' % (color, e(pwd), e(pwd))
            )
        out += '<div class="dl-row">%s%s</div>' % (url_item, pass_item)
    return out or '<div style="color:#999;font-size:13px;">暂未提供下载链接，即将更新</div>'


def render_card(im):
    return (
        '<div class="box">'
        '<div class="name"><h1>%s</h1><span class="toggle">[ 展开/收起 ]</span></div>'
        '<div class="tag">%s</div>'
        '<div class="detail">%s<div class="download">%s</div></div>'
        '</div>' % (e(im.get('title', '')), render_tags(im), render_params(im), render_links(im.get('links', [])))
    )


def render_nav(cats, active_cat, prefix):
    out = '<ul>'
    out += '<li class="%s"><a href="%sindex.html"><i class="ic"></i>首页</a></li>' % (
        'active' if active_cat == '__home__' else '', prefix)
    for c in cats:
        out += '<li class="%s"><a href="%s%s.html"><i class="ic"></i>%s</a></li>' % (
            'active' if c['id'] == active_cat else '', prefix, e(c['id']), e(c['name']))
    out += '</ul>'
    return out


def render_submenu(cat, active_ver, prefix):
    vers = cat.get('versions', [])
    if not vers:
        return ''
    latest = vers[0]['id']
    out = '<div class="submenu">'
    for v in vers:
        # 最新版本指向 <cat>.html，其余指向 <cat>/<ver>.html
        if v['id'] == latest:
            href = '%s%s.html' % (prefix, cat['id'])
        else:
            href = '%s%s/%s.html' % (prefix, cat['id'], v['id'])
        out += '<a href="%s" class="%s">%s</a>' % (href, 'active' if v['id'] == active_ver else '', e(v['name']))
    out += '</div>'
    return out


# ---------------------------------------------------------------- 页面模板
PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <meta name="keywords" content="{keywords}">
  <meta name="description" content="{desc}">
  <link rel="canonical" href="{canonical}">
  <link rel="stylesheet" href="{prefix}assets/css/style.css">
  <script>
    var _hmt = _hmt || [];
    (function () {{
      var hm = document.createElement("script");
      hm.src = "https://hm.baidu.com/hm.js?{hm}";
      var s = document.getElementsByTagName("script")[0];
      s.parentNode.insertBefore(hm, s);
    }})();
  </script>
</head>
<body>
  <div class="layout">
    <aside class="side">
      <div class="logo"><a href="{prefix}index.html">{brand}<span class="dot">.</span></a></div>
      <nav class="nav">{nav}</nav>
      <div class="side-foot">{subtitle}</div>
    </aside>
    <div class="mask" id="mask"></div>
    <div class="main">
      <header class="header">
        <div style="display:flex;align-items:center;gap:10px;">
          <div class="menu-btn" id="menu-btn"><span></span><span></span><span></span></div>
          <div class="crumb">{crumb}</div>
        </div>
        <div class="tools"><span class="muted-tip">提供网盘链接 · 原版镜像</span></div>
      </header>
      <main class="container">
{body}
      </main>
    </div>
  </div>
  <div class="toast" id="toast"></div>
  <script src="{prefix}assets/js/site.js"></script>
</body>
</html>
"""


def make_desc(cat_name, ver_name, images):
    eds = []
    for im in images[:4]:
        for x in im.get('editions', [])[:3]:
            if x not in eds:
                eds.append(x)
    ed = '、'.join(eds[:6])
    return '提供 %s %s 原版 ISO 镜像的网盘下载（夸克/百度/阿里/天翼等），%s等版本，附文件名与 SHA-256 校验值，微软官方原版未修改。' % (
        cat_name, ver_name, (ed + '，') if ed else '')


def write(path, content):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)


# ---------------------------------------------------------------- 主流程
def main():
    data = json.load(open(DATA, encoding='utf-8'))
    site = data.get('site', {})
    cats = data.get('categories', [])
    images = data.get('images', [])
    brand = e(site.get('brand', 'MacroHard'))
    subtitle = e(site.get('subtitle', ''))
    notice = site.get('notice', '')
    footer = site.get('footer', '')
    base_kw = 'Windows镜像,系统下载,网盘下载,MSDN,原版镜像,ISO下载'

    by_cat = {c['id']: [im for im in images if im.get('category') == c['id']] for c in cats}
    urls = []  # for sitemap

    def cards_block(imgs):
        if not imgs:
            return '<div class="empty"><div class="big">📦</div><div style="font-size:16px;color:#444;">暂无镜像</div><div style="margin-top:6px;">该版本还没有发布镜像</div></div>'
        return '<div class="cards">%s</div>' % ''.join(render_card(im) for im in imgs)

    def foot_block():
        return '<div class="foot">%s</div>' % e(footer)

    def notice_block():
        return ('<div class="notice">%s</div>' % e(notice)) if notice else ''

    def page(path, title, desc, keywords, active_cat, crumb, body, prefix):
        canonical = BASE_URL + '/' + path
        html_out = PAGE.format(
            title=e(title), keywords=e(keywords), desc=e(desc), canonical=e(canonical),
            prefix=prefix, hm=BAIDU_HM, brand=brand,
            nav=render_nav(cats, active_cat, prefix), subtitle=subtitle,
            crumb=crumb, body=body)
        write(path, html_out)
        urls.append(path)

    def sort_imgs(imgs):
        return sorted(imgs, key=lambda x: x.get('date', ''), reverse=True)

    # ---------- 首页 ----------
    latest = sort_imgs(images)[:15]
    cat_links = '<div class="submenu">' + ''.join(
        '<a href="%s.html">%s</a>' % (e(c['id']), e(c['name'])) for c in cats) + '</div>'
    home_body = (
        notice_block() +
        '<h2 style="font-size:15px;margin:4px 0 12px;color:#374151;">系统分类</h2>' + cat_links +
        '<h2 style="font-size:15px;margin:22px 0 12px;color:#374151;">最新镜像</h2>' +
        cards_block(latest) + foot_block()
    )
    page('index.html', e(site.get('title', 'MacroHard 系统下载')),
         subtitle + ' ' + notice, base_kw, '__home__',
         '最新镜像 <small>%s</small>' % subtitle, home_body, '')

    # ---------- 分类页 & 版本页 ----------
    for c in cats:
        cid = c['id']
        cname = c['name']
        vers = c.get('versions', [])
        imgs = by_cat.get(cid, [])
        defined = {v['id'] for v in vers}

        if vers:
            latest_ver = vers[0]
            # 分类落地页 = 最新版本 + 无版本/未知版本的兜底镜像
            land_imgs = sort_imgs([im for im in imgs if im.get('version') == latest_ver['id']
                                   or im.get('version', '') == '' or im.get('version') not in defined])
            crumb = '%s <small>%s</small>' % (e(cname), e(latest_ver['name']))
            body = notice_block() + render_submenu(c, latest_ver['id'], '') + cards_block(land_imgs) + foot_block()
            page('%s.html' % cid,
                 '%s %s 原版镜像下载 - %s系统下载' % (cname, latest_ver['name'], brand),
                 make_desc(cname, latest_ver['name'], land_imgs),
                 '%s,%s %s,%s' % (cname, cname, latest_ver['name'], base_kw),
                 cid, crumb, body, '')

            # 其余版本页
            for v in vers[1:]:
                v_imgs = sort_imgs([im for im in imgs if im.get('version') == v['id']])
                crumb = '%s <small>%s</small>' % (e(cname), e(v['name']))
                body = notice_block() + render_submenu(c, v['id'], '../') + cards_block(v_imgs) + foot_block()
                page('%s/%s.html' % (cid, v['id']),
                     '%s %s 原版镜像下载 - %s系统下载' % (cname, v['name'], brand),
                     make_desc(cname, v['name'], v_imgs),
                     '%s,%s %s,%s' % (cname, cname, v['name'], base_kw),
                     cid, crumb, body, '../')
        else:
            all_imgs = sort_imgs(imgs)
            crumb = '%s <small>%s</small>' % (e(cname), subtitle)
            body = notice_block() + cards_block(all_imgs) + foot_block()
            page('%s.html' % cid,
                 '%s 原版镜像下载 - %s系统下载' % (cname, brand),
                 make_desc(cname, '', all_imgs),
                 '%s,%s' % (cname, base_kw),
                 cid, crumb, body, '')

    # ---------- sitemap.xml ----------
    today = datetime.date.today().isoformat()
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        loc = BASE_URL + '/' + ('' if u == 'index.html' else u)
        pr = '1.0' if u == 'index.html' else '0.8'
        sm.append('  <url><loc>%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>' % (e(loc), today, pr))
    sm.append('</urlset>')
    write('sitemap.xml', '\n'.join(sm) + '\n')

    # ---------- robots.txt ----------
    write('robots.txt', 'User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n' % BASE_URL)

    print('已生成 %d 个页面：' % len(urls))
    for u in urls:
        print('  ', u)


if __name__ == '__main__':
    main()
