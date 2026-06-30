# MacroHard 系统下载站

一个部署在 GitHub Pages 上的 Windows / Office 原版镜像**网盘下载站**，外加一个**仅在本地使用**的镜像管理后台。
仿 `msdn.sjjzm.com` 的界面，但**只提供网盘下载链接**（用于网盘推广），且增删改镜像**无需手动改 HTML / 手动上传仓库**——
本地后台直接通过 GitHub API 把改动提交回仓库，GitHub Pages 自动更新。

```
macrohard0.github.io/
├── index.html              # 前台下载站（数据驱动单页应用）—— 发布到 Pages
├── admin/
│   └── index.html          # 镜像管理后台（纯网页，连接 GitHub）—— ⚠️ 仅本地用，不发布
├── assets/
│   ├── css/style.css       # 前台样式
│   └── js/
│       ├── config.js       # 网盘类型 / 参数字段（前后台共用）
│       └── render.js       # 前台渲染逻辑
├── data/
│   └── images.json         # 全部数据：站点信息 + 分类 + 镜像（后台唯一改动的文件）
├── .gitignore              # 已排除 admin/，确保后台不会被推到公开仓库
└── README.md
```

**核心思路**：所有镜像信息都在 `data/images.json` 里，页面运行时读取并渲染。
后台只编辑这一个 JSON 文件，所以「加镜像 / 改链接 / 删镜像」永远不需要碰 HTML。

> 🔒 **安全模型**：管理后台是静态页，前端密码可被绕过，不算强保护。本项目采取更彻底的做法——
> 通过 `.gitignore` 让 `admin/` **不发布到 GitHub**，外人在 `macrohard0.github.io/admin/` 只会得到 404。
> 你始终在**本地**打开后台来管理；真正的写权限锁是 **GitHub Token**（只存在你本机浏览器，从不上传）。

---

## 一、部署到 GitHub Pages

1. 在 GitHub 新建仓库，名字必须是 **`macrohard0.github.io`**（用户名 + `.github.io`）。
2. 把本目录文件推送到该仓库的 `main` 分支（`.gitignore` 会自动跳过 `admin/`，后台不会上线）：
   ```bash
   cd E:/sherlock/macrohard0
   git init
   git add .
   git commit -m "init: MacroHard 系统下载站"
   git branch -M main
   git remote add origin https://github.com/macrohard0/macrohard0.github.io.git
   git push -u origin main
   ```
   推送后可执行 `git ls-files` 确认列表里**没有** `admin/index.html`。
3. 仓库 **Settings → Pages → Build and deployment**：Source 选 `Deploy from a branch`，分支选 `main` / 根目录 `/`。
4. 等 1~2 分钟，访问前台：**https://macrohard0.github.io/**
   （`https://macrohard0.github.io/admin/` 应为 404，这是正常的——后台只在本地用。）

> 本地预览前台：因为前台用 `fetch` 读取 JSON，直接双击 `index.html` 会被浏览器拦截。
> 请在本目录执行 `python -m http.server 8080`，再访问 `http://localhost:8080/`。

---

## 二、生成 GitHub Token（后台提交需要）

后台要把改动写回仓库，需要一个有写权限的 Token：

1. 打开 https://github.com/settings/tokens
2. 推荐用 **Fine-grained token**：
   - Repository access：只选 `macrohard0.github.io`
   - Permissions → Repository permissions → **Contents：Read and write**
3. 生成后复制 `github_pat_...`（或经典 token `ghp_...`，勾选 `repo` 即可）。

> Token 只保存在你本机浏览器的 localStorage，不会上传到任何服务器。
> 换电脑 / 清缓存后需要重新填。Token 泄露可随时在上面页面 Revoke。

---

## 三、使用管理后台（本地）

后台**不发布**，在本机打开即可。两种打开方式：

- **方式 A（最简单）**：直接双击 `admin/index.html` 用浏览器打开。
- **方式 B（更稳，推荐）**：在本目录执行 `python -m http.server 8080`，访问 `http://localhost:8080/admin/`。
  （个别浏览器对 `file://` 下的网络请求较严格，用本地服务器最稳妥。）

> 后台读写的是 **GitHub 上的 `data/images.json`**（通过 API），不是你本地那份。
> 也就是说：本地编辑 → 点保存推到 GitHub → 公开前台自动更新。本地这份 `data/images.json` 只在你本地预览前台时用到。

打开后按顺序操作：

### ① 连接 GitHub
- 用户名 `macrohard0`，仓库 `macrohard0.github.io`，分支 `main`，路径 `data/images.json`（已是默认值）。
- 粘贴 Token，点 **「记住设置」**（下次免填），再点 **「连接并加载数据」**。
- 状态变绿即表示数据已拉取成功。

### ② 增 / 改 / 删镜像
- **新增镜像**：填标题、选分类/版本、架构、语言、日期、版本标签；填文件参数（文件名 / SHA-256 / SHA-1 / MD5 / 文件大小）；
  点 **「+ 添加网盘」** 逐个加网盘链接（选网盘类型 + 链接 + 可选提取码）。
- **编辑**：列表里点对应镜像的「编辑」。
- **删除**：列表里点「删除」，或在编辑弹窗里点「删除此镜像」。
- **管理分类**：增删分类、给分类配版本子菜单（如 Windows 11 下的 26H1 / 25H2）。

> 以上操作都只改动**浏览器里的临时副本**，右上角会出现「● 有未保存改动」。

### ③ 保存上线
- 点 **「💾 保存到 GitHub」**，后台会把整个 `data/images.json` 提交回仓库。
- 等 GitHub Pages 重新发布（约 1 分钟），刷新前台即可看到。

### 备份手段
- **导出 JSON**：随时下载当前数据做备份。
- **导入 JSON**：从备份文件恢复 / 离线编辑后再导入。

---

## 四、支持的网盘类型

在 `assets/js/config.js` 的 `PAN_TYPES` 里定义，前后台共用。默认包含：

| key | 名称 | 默认带提取码 |
|------|--------|------|
| quark | 夸克网盘 | 否 |
| baidu | 百度网盘 | 是 |
| aliyun | 阿里云盘 | 否 |
| tianyi | 天翼云盘 | 是 |
| xunlei | 迅雷网盘 | 是 |
| weiyun | 腾讯微云 | 否 |
| yidong | 移动云盘 | 否 |
| pan123 | 123云盘 | 否 |
| other | 其他网盘 | 是 |

**新增一种网盘**：在 `PAN_TYPES` 加一条 `key:{name,color,needPassword,hint}` 即可，前台展示与后台下拉会自动出现。
（任何网盘都能手动填提取码，`needPassword` 只是默认提示。）

---

## 五、数据结构 `data/images.json`

```jsonc
{
  "site": { "title":"...", "subtitle":"...", "brand":"MacroHard", "footer":"...", "notice":"..." },
  "categories": [
    { "id":"win11", "name":"Windows 11",
      "versions":[ {"id":"26h1","name":"26H1"} ] }
  ],
  "images": [
    {
      "id": "唯一标识",
      "category": "win11",        // 对应某个 categories.id
      "version": "26h1",          // 对应该分类的 versions.id，可留空
      "title": "Windows 11 ... x64",
      "arch": "64位",
      "lang": "中文简体",
      "date": "2026-06-16",
      "editions": ["专业版","家庭版"],
      "params": { "文件名":"...","SHA-256":"...","SHA-1":"...","MD5":"...","文件大小":"7.64GB" },
      "links": [
        { "type":"quark", "url":"https://pan.quark.cn/s/xxx", "password":"" },
        { "type":"baidu", "url":"https://pan.baidu.com/s/xxx", "password":"msdn" }
      ]
    }
  ]
}
```

> 种子数据里的示例链接（`...example...`、全 0 的校验值）是占位用的，上线前请在后台替换成真实网盘链接与校验值。

---

## 六、前台说明

- 左侧导航 = `categories`；分类页顶部子菜单 = 该分类的 `versions`；首页按日期倒序展示全部镜像。
- 路由用 URL hash：`#win11`、`#win11/26h1`、`#home`，刷新不丢失、可直接分享。
- 每个网盘有「复制链接 / 打开」，有提取码时单独给「复制提取码」。
- 移动端侧栏自动收起为汉堡菜单。
