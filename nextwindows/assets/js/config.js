/*
 * 全站共享配置：网盘类型定义。
 * 前台 (render.js) 与 管理工具 (admin/index.html) 都引用本文件，
 * 保证两边的网盘种类、显示名称、颜色、是否需要提取码完全一致。
 *
 * 想新增一种网盘：在 PAN_TYPES 里加一条即可，前台与后台会自动出现。
 *   key          —— 存进 data.json 的类型标识（英文，勿改已用的）
 *   name         —— 显示名称
 *   color        —— 标签/按钮主题色
 *   needPassword —— 该网盘默认是否带提取码（管理工具会据此显示密码框；任何网盘也都可手动加密码）
 *   hint         —— URL 占位提示，方便录入时辨认
 */
window.PAN_TYPES = {
  quark:  { name: '夸克网盘',   color: '#2D5BFF', needPassword: false, hint: 'https://pan.quark.cn/s/...' },
  baidu:  { name: '百度网盘',   color: '#06A7FF', needPassword: true,  hint: 'https://pan.baidu.com/s/...' },
  aliyun: { name: '阿里云盘',   color: '#FF6A00', needPassword: false, hint: 'https://www.alipan.com/s/...' },
  tianyi: { name: '天翼云盘',   color: '#D9001B', needPassword: true,  hint: 'https://cloud.189.cn/t/...' },
  xunlei: { name: '迅雷网盘',   color: '#1B7BFF', needPassword: true,  hint: 'https://pan.xunlei.com/s/...' },
  weiyun: { name: '腾讯微云',   color: '#00C250', needPassword: false, hint: 'https://share.weiyun.com/...' },
  yidong: { name: '移动云盘',   color: '#3A8FFF', needPassword: false, hint: 'https://caiyun.139.com/...' },
  pan123: { name: '123云盘',    color: '#2A66FF', needPassword: false, hint: 'https://www.123pan.com/s/...' },
  terabox: { name: 'TeraBox',   color: '#0F6FFF', needPassword: false, hint: 'https://1024terabox.com/s/...' },
  other:  { name: '其他网盘',   color: '#7A7F8C', needPassword: true,  hint: 'https://...' }
};

// 取网盘类型信息，未知类型回退到“其他网盘”
window.panType = function (key) {
  return window.PAN_TYPES[key] || window.PAN_TYPES.other;
};

// 默认网盘排序（前台展示与管理工具下拉的顺序）
window.PAN_ORDER = ['quark', 'baidu', 'aliyun', 'tianyi', 'xunlei', 'weiyun', 'yidong', 'pan123', 'terabox', 'other'];

// 参数表的标准字段（顺序即展示顺序）。管理工具按此渲染输入框。
window.PARAM_FIELDS = ['文件名', 'SHA-256', 'SHA-1', 'MD5', '文件大小'];

/*
 * 分类（categories）的 lang 字段 —— 决定该分类归属哪个语言子站，build.py 据此分流生成
 * /、/en-us/ 等目录。管理工具的「管理分类」用它来选择语言；未设置 = zh-cn（默认/根目录）。
 * 要新增语言子站：先在 data/config.json 的 languages 里加一条，再在这里加对应的显示名
 * 和网盘白名单（若有限制），两边保持一致。
 */
window.LANG_LABELS = { 'zh-cn': '中文（默认 /）', 'en-us': 'English (/en-us/)' };
window.LANG_ORDER = ['zh-cn', 'en-us'];

// 各语言子站允许使用的网盘 provider 白名单；未列出的语言 = 不限制（默认所有语言都不限制）。
// 与 data/config.json 的 languages[].panProviders 保持一致——那边才是 build.py 真正读取的配置，
// 这里只是给管理工具做录入时的提示，两边改的时候别忘了同步。
window.LANG_PAN_LIMIT = {};
