#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
静态站点生成器 —— 从 data/images.json + data/config.json 生成对搜索引擎友好的静态 HTML。

用法：
    python build.py

产物 —— 同一份内容生成两套，各自独立、互不引用：
    仓库根目录            SITES 里 out_dir='' 那套，供 macrohard0.github.io（GitHub Pages）托管
    nextwindows/ 子目录    SITES 里 out_dir='nextwindows' 那套，供新域名 nextwindows.org 独立部署
每套内部再按语言分子目录（data/config.json 的 languages 配置）：
    /                          默认语言（zh-cn，dir=""）—— 与旧版路径完全一致
    /<lang.dir>/               其余语言（如 en-us）的首页、分类页、版本页，结构与默认语言一致
每套各自包含：
    index.html                首页
    <cat>.html                分类页（= 该分类最新版本，如 win11.html = 26H1）
    <cat>/<ver>.html          各历史版本页（如 win11/25h2.html）
    <lang>/index.html         非默认语言的首页（如 en-us/index.html）
    <lang>/<cat>.html         非默认语言的分类页
    <lang>/<cat>/<ver>.html   非默认语言的版本页
    sitemap.xml               站点地图（含所有语言子目录，域名对应各自的 base_url）
    robots.txt                （Sitemap 行指向各自域名）
    assets/                   css/js 静态资源的独立拷贝（各语言子目录共用同一份）

设计要点：
    - 内容在服务端就渲染进 HTML（利于收录），导航用真实 <a> 链接
    - 分类（categories）自带 lang 字段决定归属哪个语言子站；不写 lang 视为默认语言 zh-cn，
      因此已有分类/镜像数据无需改动，后台管理工具 admin/index.html 也无需跟着改
    - 非默认语言的网盘 provider 白名单在 config.json 的 languages[].panProviders 里配置
      （目前英文站只放开 terabox），生成时会过滤掉不在白名单内的链接
    - brand（站点名）与域名绑定、跨语言保持不变；非默认语言的首页标题按模板由 brand 生成，
      subtitle/footer/notice 等文案可在 config.json 对应语言里覆盖
    - 复用现有 assets/css/style.css；复制/展开/移动端菜单交给 assets/js/site.js（渐进增强）
    - 下载链接来自 images.json；外链加 rel="nofollow"
    - 路径按页面深度用相对前缀（本地 file://、localhost、根域名都能跑）
"""
import json, os, html, shutil, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, 'data', 'images.json')
CONFIG = os.path.join(ROOT, 'data', 'config.json')

# 每一项生成一整套独立站点：out_dir 相对仓库根目录（''=根目录本身）
# hm 是各自站点在百度统计后台登记的站点 ID（不同域名要分开统计，不能共用）
SITES = [
    {
        'base_url': 'https://macrohard0.github.io',
        'out_dir': '',
        'hm': '54f24ee5c82c27e994fb615aa3173346',
        'brand': 'MacroHard',
        'title': 'MacroHard 系统下载',
    },
    {
        'base_url': 'https://nextwindows.org',
        'out_dir': 'nextwindows',
        'hm': 'f054e0121b69929417e9535aef70567c',
        'brand': 'NextWindows',
        'title': 'NextWindows 系统下载',
    },
]

DEFAULT_LANG = 'zh-cn'

# 与 assets/js/config.js 的 PAN_TYPES 保持一致（改这里也要改那边）
PAN = {
    'quark':   ('夸克网盘', '#2D5BFF'),
    'baidu':   ('百度网盘', '#06A7FF'),
    'aliyun':  ('阿里云盘', '#FF6A00'),
    'tianyi':  ('天翼云盘', '#D9001B'),
    'xunlei':  ('迅雷网盘', '#1B7BFF'),
    'weiyun':  ('腾讯微云', '#00C250'),
    'yidong':  ('移动云盘', '#3A8FFF'),
    'pan123':  ('123云盘',  '#2A66FF'),
    'terabox': ('TeraBox',  '#0F6FFF'),
    'other':   ('其他网盘', '#7A7F8C'),
}
def pan(t):
    return PAN.get(t, PAN['other'])

PARAM_FIELDS = ['文件名', 'SHA-256', 'SHA-1', 'MD5', '文件大小']
# 参数表字段的展示名按语言翻译；im['params'] 的 key 本身（中文）不变，admin 工具也不用改
PARAM_LABELS = {
    'zh-cn': {'文件名': '文件名', 'SHA-256': 'SHA-256', 'SHA-1': 'SHA-1', 'MD5': 'MD5', '文件大小': '文件大小'},
    'en-us': {'文件名': 'File name', 'SHA-256': 'SHA-256', 'SHA-1': 'SHA-1', 'MD5': 'MD5', '文件大小': 'File size'},
}

# 每种语言的界面文案（导航、按钮、提示语、标题/描述模板等）
STRINGS = {
    'zh-cn': dict(
        code='zh-cn', html_lang='zh-CN',
        home='首页', toggle='[ 展开/收起 ]',
        copy_link='复制链接', open_link='打开', extract_code='提取码', copy='复制',
        no_link='暂未提供下载链接，即将更新',
        no_image_title='暂无镜像', no_image_sub='该版本还没有发布镜像',
        os_categories='系统分类', latest_images='最新镜像', header_tip='提供网盘链接 · 原版镜像',
        base_kw='Windows镜像,系统下载,网盘下载,MSDN,原版镜像,ISO下载',
        home_title_tmpl='%s 系统下载',
        title_ver_tmpl='%s %s 原版镜像下载 - %s系统下载',
        title_plain_tmpl='%s 原版镜像下载 - %s系统下载',
        desc_tmpl='提供 %s %s 原版 ISO 镜像的网盘下载（夸克/百度/阿里/天翼等），%s等版本，附文件名与 SHA-256 校验值，微软官方原版未修改。',
    ),
    'en-us': dict(
        code='en-us', html_lang='en-US',
        home='Home', toggle='[ Expand/Collapse ]',
        copy_link='Copy Link', open_link='Open', extract_code='Password', copy='Copy',
        no_link='No download link yet, check back soon',
        no_image_title='No images yet', no_image_sub='No images have been published for this version yet',
        os_categories='OS Categories', latest_images='Latest Images', header_tip='Cloud drive links · Original images',
        base_kw='Windows ISO,Windows download,original image,MSDN,ISO download,cloud drive',
        home_title_tmpl='%s ISO Downloads',
        title_ver_tmpl='%s %s Original ISO Download - %s',
        title_plain_tmpl='%s Original ISO Download - %s',
        desc_tmpl='Download the original %s %s ISO image via cloud drive (TeraBox), covering %sversions, with filename and SHA-256 checksum. Unmodified official Microsoft image.',
    ),
}
def strings(lang):
    return STRINGS.get(lang, STRINGS[DEFAULT_LANG])


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


def render_params(im, t):
    rows = ''
    p = im.get('params', {}) or {}
    labels = PARAM_LABELS.get(t['code'], PARAM_LABELS[DEFAULT_LANG])
    for k in PARAM_FIELDS:
        v = p.get(k)
        if v:
            rows += '<tr><td class="param-name">%s</td><td class="param-value">%s</td></tr>' % (e(labels.get(k, k)), e(v))
    if not rows:
        return ''
    return '<table class="param"><tbody>%s</tbody></table>' % rows


def render_links(links, t, pan_allowed=None):
    if pan_allowed is not None:
        links = [lk for lk in (links or []) if lk.get('type') in pan_allowed]
    if not links:
        return '<div style="color:#999;font-size:13px;">%s</div>' % e(t['no_link'])
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
            '<button class="dl-copy" data-copy="%s">%s</button>'
            '<button class="dl-open" data-open="%s">%s</button>'
            '</div>' % (color, e(name), e(url), e(url), e(t['copy_link']), e(url), e(t['open_link']))
        )
        pass_item = ''
        if pwd:
            pass_item = (
                '<div class="dl-item pass">'
                '<div class="dl-label" style="background:%s">%s</div>'
                '<input class="dl-input" readonly value="%s">'
                '<button class="dl-copy" data-copy="%s">%s</button>'
                '</div>' % (color, e(t['extract_code']), e(pwd), e(pwd), e(t['copy']))
            )
        out += '<div class="dl-row">%s%s</div>' % (url_item, pass_item)
    return out or '<div style="color:#999;font-size:13px;">%s</div>' % e(t['no_link'])


def render_card(im, t, pan_allowed=None):
    return (
        '<div class="box">'
        '<div class="name"><h3>%s</h3><span class="toggle">%s</span></div>'
        '<div class="tag">%s</div>'
        '<div class="detail">%s<div class="download">%s</div></div>'
        '</div>' % (e(im.get('title', '')), e(t['toggle']), render_tags(im),
                    render_params(im, t), render_links(im.get('links', []), t, pan_allowed))
    )


def render_nav(cats, active_cat, prefix, t):
    out = '<ul>'
    out += '<li class="%s"><a href="%sindex.html"><i class="ic"></i>%s</a></li>' % (
        'active' if active_cat == '__home__' else '', prefix, e(t['home']))
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
<html lang="{html_lang}">
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
      <div class="logo"><a href="{home_prefix}index.html">{brand}<span class="dot">.</span></a></div>
      <nav class="nav">{nav}</nav>
      <div class="side-foot">{subtitle}</div>
    </aside>
    <div class="mask" id="mask"></div>
    <div class="main">
      <header class="header">
        <div style="display:flex;align-items:center;gap:10px;">
          <div class="menu-btn" id="menu-btn"><span></span><span></span><span></span></div>
          <h1 class="crumb">{crumb}</h1>
        </div>
        <div class="tools"><span class="muted-tip">{header_tip}</span></div>
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


def make_desc(cat_name, ver_name, images, t):
    eds = []
    for im in images[:4]:
        for x in im.get('editions', [])[:3]:
            if x not in eds:
                eds.append(x)
    if t['code'] == 'zh-cn':
        ed = '、'.join(eds[:6])
        ed_part = (ed + '，') if ed else ''
    else:
        ed = ', '.join(eds[:6])
        ed_part = (ed + ', ') if ed else ''
    return t['desc_tmpl'] % (cat_name, ver_name, ed_part)


def write(out_root, path, content):
    full = os.path.join(out_root, path)
    os.makedirs(os.path.dirname(full) or out_root, exist_ok=True)
    with open(full, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)


# ---------------------------------------------------------------- 单套站点
def build_site(base_url, out_dir, hm, data, config, site_overrides=None):
    out_root = os.path.join(ROOT, out_dir) if out_dir else ROOT
    site_overrides = site_overrides or {}
    site_base = data.get('site', {})
    all_cats = data.get('categories', [])
    all_images = data.get('images', [])
    brand_plain = site_overrides.get('brand') or site_base.get('brand', 'NextWindows')
    brand = e(brand_plain)

    urls = []  # for sitemap（相对 out_root 的路径，含各语言子目录前缀）
    home_paths = set()  # 各语言首页的 path（'index.html' / 'en-us/index.html' ...），sitemap 特殊处理

    languages = config.get('languages') or [{'code': DEFAULT_LANG, 'dir': ''}]
    for lang_conf in languages:
        code = lang_conf.get('code', DEFAULT_LANG)
        t = strings(code)
        is_default = (code == DEFAULT_LANG)
        lang_dir = (lang_conf.get('dir') or '').strip('/')
        # 该语言子目录相对 out_root 的层级深度（把「资源前缀」换算成「同语言子站内前缀」要用）
        lang_depth = (lang_dir.count('/') + 1) if lang_dir else 0
        pan_allowed = set(lang_conf['panProviders']) if lang_conf.get('panProviders') else None

        lang_site_over = lang_conf.get('site') or {}
        site = dict(site_base)
        site.update(lang_site_over)
        if is_default:
            home_title = site_overrides.get('title') or site_base.get('title') or (t['home_title_tmpl'] % brand_plain)
        else:
            home_title = lang_site_over.get('title') or (t['home_title_tmpl'] % brand_plain)

        subtitle = e(site.get('subtitle', ''))
        notice = site.get('notice', '')
        footer = site.get('footer', '')
        base_kw = t['base_kw']

        cats = [c for c in all_cats if (c.get('lang') or DEFAULT_LANG) == code]
        cat_ids = {c['id'] for c in cats}
        images = [im for im in all_images if im.get('category') in cat_ids]
        by_cat = {c['id']: [im for im in images if im.get('category') == c['id']] for c in cats}

        def p(name):
            return (lang_dir + '/' + name) if lang_dir else name

        def asset_prefix_for(path):
            return '../' * path.count('/')

        def section_prefix_for(path):
            return '../' * (path.count('/') - lang_depth)

        def cards_block(imgs):
            if not imgs:
                return ('<div class="empty"><div class="big">📦</div>'
                        '<div style="font-size:16px;color:#444;">%s</div>'
                        '<div style="margin-top:6px;">%s</div></div>') % (e(t['no_image_title']), e(t['no_image_sub']))
            return '<div class="cards">%s</div>' % ''.join(render_card(im, t, pan_allowed) for im in imgs)

        def foot_block():
            return '<div class="foot">%s</div>' % e(footer)

        def notice_block():
            return ('<div class="notice">%s</div>' % e(notice)) if notice else ''

        def page(path, title, desc, keywords, active_cat, crumb, body):
            asset_prefix = asset_prefix_for(path)
            home_prefix = section_prefix_for(path)
            canonical = base_url + '/' + path
            html_out = PAGE.format(
                html_lang=t['html_lang'],
                title=e(title), keywords=e(keywords), desc=e(desc), canonical=e(canonical),
                prefix=asset_prefix, home_prefix=home_prefix, hm=hm, brand=brand,
                nav=render_nav(cats, active_cat, home_prefix, t), subtitle=subtitle,
                header_tip=e(t['header_tip']),
                crumb=crumb, body=body)
            write(out_root, path, html_out)
            urls.append(path)

        def sort_imgs(imgs):
            return sorted(imgs, key=lambda x: x.get('date', ''), reverse=True)

        # ---------- 首页 ----------
        latest = sort_imgs(images)[:15]
        cat_links = '<div class="submenu">' + ''.join(
            '<a href="%s.html">%s</a>' % (e(c['id']), e(c['name'])) for c in cats) + '</div>'
        home_body = (
            notice_block() +
            '<h2 style="font-size:15px;margin:4px 0 12px;color:#374151;">%s</h2>' % e(t['os_categories']) + cat_links +
            '<h2 style="font-size:15px;margin:22px 0 12px;color:#374151;">%s</h2>' % e(t['latest_images']) +
            cards_block(latest) + foot_block()
        )
        home_path = p('index.html')
        page(home_path, e(home_title),
             subtitle + ' ' + notice, base_kw, '__home__',
             '%s <small>%s</small>' % (e(t['latest_images']), subtitle), home_body)
        home_paths.add(home_path)

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
                # 注意：这里不按日期重新排序，保留 images.json 里的原始顺序——
                # 管理后台的拖拽调整顺序就是靠这个顺序生效的
                land_imgs = [im for im in imgs if im.get('version') == latest_ver['id']
                             or im.get('version', '') == '' or im.get('version') not in defined]
                crumb = '%s <small>%s</small>' % (e(cname), e(latest_ver['name']))
                cat_path = p('%s.html' % cid)
                body = notice_block() + render_submenu(c, latest_ver['id'], section_prefix_for(cat_path)) + cards_block(land_imgs) + foot_block()
                page(cat_path,
                     t['title_ver_tmpl'] % (cname, latest_ver['name'], brand),
                     make_desc(cname, latest_ver['name'], land_imgs, t),
                     '%s,%s %s,%s' % (cname, cname, latest_ver['name'], base_kw),
                     cid, crumb, body)

                # 其余版本页
                for v in vers[1:]:
                    v_imgs = [im for im in imgs if im.get('version') == v['id']]
                    crumb = '%s <small>%s</small>' % (e(cname), e(v['name']))
                    ver_path = p('%s/%s.html' % (cid, v['id']))
                    body = notice_block() + render_submenu(c, v['id'], section_prefix_for(ver_path)) + cards_block(v_imgs) + foot_block()
                    page(ver_path,
                         t['title_ver_tmpl'] % (cname, v['name'], brand),
                         make_desc(cname, v['name'], v_imgs, t),
                         '%s,%s %s,%s' % (cname, cname, v['name'], base_kw),
                         cid, crumb, body)
            else:
                all_imgs = imgs
                crumb = '%s <small>%s</small>' % (e(cname), subtitle)
                body = notice_block() + cards_block(all_imgs) + foot_block()
                page(p('%s.html' % cid),
                     t['title_plain_tmpl'] % (cname, brand),
                     make_desc(cname, '', all_imgs, t),
                     '%s,%s' % (cname, base_kw),
                     cid, crumb, body)

    # ---------- sitemap.xml ----------
    today = datetime.date.today().isoformat()
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        is_home = u in home_paths
        loc = base_url + '/' + (u[:-len('index.html')] if is_home else u)
        pr = '1.0' if is_home else '0.8'
        sm.append('  <url><loc>%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>' % (e(loc), today, pr))
    sm.append('</urlset>')
    write(out_root, 'sitemap.xml', '\n'.join(sm) + '\n')

    # ---------- robots.txt ----------
    write(out_root, 'robots.txt', 'User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n' % base_url)

    # ---------- assets（css/js）独立拷贝 ----------
    if out_root != ROOT:
        shutil.copytree(os.path.join(ROOT, 'assets'), os.path.join(out_root, 'assets'), dirs_exist_ok=True)

    print('[%s] 已生成 %d 个页面：' % (base_url, len(urls)))
    for u in urls:
        print('  ', u)


# ---------------------------------------------------------------- 主流程
def main():
    data = json.load(open(DATA, encoding='utf-8'))
    if os.path.exists(CONFIG):
        config = json.load(open(CONFIG, encoding='utf-8'))
    else:
        config = {'languages': [{'code': DEFAULT_LANG, 'dir': ''}]}
    for s in SITES:
        build_site(
            s['base_url'], s['out_dir'], s['hm'], data, config,
            {'brand': s.get('brand'), 'title': s.get('title')},
        )


if __name__ == '__main__':
    main()
