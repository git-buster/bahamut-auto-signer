# Bahamut Secret Refresher Helper

## 繁體中文

這是一個公開工具包，提供兩個命令：

```text
bahamut-cookie-exporter
bahamut-secret-refresher
```

`bahamut-cookie-exporter` 用來在本機開啟 Chromium，讓使用者手動登入巴哈姆特後匯出 Cookie JSON。  
`bahamut-secret-refresher` 用來在 GitHub Actions 裡，把 workflow 捕獲到的新 Cookie 寫回 GitHub Actions Secret。

公開 repository 只應該放工具程式與教學文件。不要提交真實 Cookie、Token、密碼、Cookie JSON 檔案、瀏覽器 profile 或私人 workflow。

### 安裝

如果直接使用這個公開工具：

```bash
python -m pip install "git+https://github.com/git-buster/bahamut-auto-signer.git[export]"
```

如果你 fork 或複製成自己的公開 repository，請把 `OWNER/REPO` 換成你的 repository：

```bash
python -m pip install "git+https://github.com/OWNER/REPO.git[export]"
```

### 匯出 Cookie JSON

在自己的電腦執行：

```bash
bahamut-cookie-exporter
```

工具會開啟 Chromium，依序前往：

```text
https://www.gamer.com.tw/
https://www.gamer.com.tw/dailySign.php
https://guild.gamer.com.tw/
https://ani.gamer.com.tw/
```

你需要在瀏覽器裡正常登入。每個頁面確認登入後，回到終端機按 Enter，工具會輸出：

```text
baha_cookie_www.json   -> BAHA_COOKIE_JSON
baha_cookie_daily.json -> BAHA_DAILY_COOKIE_JSON
baha_cookie_guild.json -> BAHA_GUILD_COOKIE_JSON
baha_cookie_ani.json   -> BAHA_ANIME_COOKIE_JSON
```

把 JSON 檔案內容完整貼到私人 workflow repository 的 GitHub Actions Secrets。不要把 JSON 檔案提交到 GitHub。

如果你下載了原始碼，也可以這樣執行：

```bash
python -m pip install DrissionPage
python tools/export_bahamut_cookies.py
```

### 自動更新 Cookie 的原理

第一次使用時，你手動把 `BAHA_COOKIE_JSON` 放到私人 workflow repository 的 Secrets。

workflow 執行簽到時，如果程式捕獲到新的 Cookie，會把它寫到 runner 的暫存檔。接著 `bahamut-secret-refresher` 會把這個暫存檔內容更新到：

```text
BAHA_REFRESHED_COOKIE
BAHA_REFRESHED_DAILY_COOKIE
BAHA_REFRESHED_GUILD_COOKIE
```

下一次 workflow 會優先使用 `BAHA_REFRESHED_COOKIE`、`BAHA_REFRESHED_DAILY_COOKIE` 和 `BAHA_REFRESHED_GUILD_COOKIE`。如果其中一個失效，刪除失效的 Secret，重新匯出 Cookie JSON，更新對應的 `BAHA_COOKIE_JSON`、`BAHA_DAILY_COOKIE_JSON` 或 `BAHA_GUILD_COOKIE_JSON`。

建議保留這種結構：

```text
BAHA_COOKIE_JSON       手動匯出的完整 Cookie JSON
BAHA_REFRESHED_COOKIE  workflow 自動更新的一行 Cookie
BAHA_DAILY_COOKIE_JSON 每日簽到專用 Cookie JSON
BAHA_REFRESHED_DAILY_COOKIE  workflow 自動更新的一行每日簽到 Cookie
BAHA_GUILD_COOKIE_JSON 手動匯出的完整公會 Cookie JSON
BAHA_REFRESHED_GUILD_COOKIE  workflow 自動更新的一行公會 Cookie
```

不要直接用一行 Cookie 覆蓋完整的 `BAHA_COOKIE_JSON`。

### 建立 GitHub Token

自動更新 GitHub Actions Secret 需要一個 Fine-grained personal access token。建立路徑：

```text
GitHub > Settings > Developer settings > Personal access tokens > Fine-grained tokens > Generate new token
```

建議設定：

```text
Repository access:
  Only selected repositories

Selected repository:
  你的私人 workflow repository

Repository permissions:
  Secrets: Read and write
  Metadata: Read-only
```

把 Token 保存到私人 workflow repository 的 Secret：

```text
BAHA_SECRET_UPDATE_TOKEN
```

### Secret 更新命令

`bahamut-secret-refresher` 需要這些環境變數：

| 名稱 | 必填 | 說明 |
| --- | --- | --- |
| `SECRET_UPDATE_TOKEN` | 是 | 可以更新 repository Secrets 的 Fine-grained Token。 |
| `TARGET_REPOSITORY` | 是 | 目標 repository，格式為 `OWNER/REPO`。 |
| `SECRET_NAME` | 是 | 要建立或更新的 Secret 名稱。 |
| `SECRET_FILE` | 否 | 存放新 Secret 值的檔案。 |
| `SECRET_VALUE` | 否 | 直接提供的新 Secret 值；未設定 `SECRET_FILE` 時使用。 |

先用無害值測試：

```bash
export SECRET_UPDATE_TOKEN="your fine-grained token"
export TARGET_REPOSITORY="OWNER/PRIVATE_WORKFLOW_REPO"
export SECRET_NAME="TEST_AUTO_UPDATED_SECRET"
export SECRET_VALUE="hello"
bahamut-secret-refresher
```

確認測試 Secret 可以建立後，再接入真實 workflow。

### 限制

這個工具不能保證 Cookie 永久有效。它只能在目前登入狀態仍被網站接受、且 workflow 捕獲到新 Cookie 時，幫你把新值保存起來。

它不能處理：

- 網站要求完整重新登入
- CAPTCHA、二次驗證或 Cloudflare 驗證
- 伺服器端主動撤銷 session
- GitHub Token 過期或權限不足

## English

This public package provides two commands:

```text
bahamut-cookie-exporter
bahamut-secret-refresher
```

`bahamut-cookie-exporter` opens Chromium locally so users can log in manually and export Bahamut Cookie JSON.  
`bahamut-secret-refresher` updates a GitHub Actions Secret from a workflow after a refreshed Cookie is captured.

The public repository should contain only tools and user documentation. Do not commit real Cookies, tokens, passwords, Cookie JSON files, browser profiles, or private workflows.

### Install

If you use this public tool directly:

```bash
python -m pip install "git+https://github.com/git-buster/bahamut-auto-signer.git[export]"
```

If you fork or copy it to your own public repository, replace `OWNER/REPO`:

```bash
python -m pip install "git+https://github.com/OWNER/REPO.git[export]"
```

### Export Cookie JSON

Run locally:

```bash
bahamut-cookie-exporter
```

The tool opens Chromium and visits:

```text
https://www.gamer.com.tw/
https://www.gamer.com.tw/dailySign.php
https://guild.gamer.com.tw/
https://ani.gamer.com.tw/
```

Log in normally in the browser. After each page is logged in, return to the terminal and press Enter. The tool writes:

```text
baha_cookie_www.json   -> BAHA_COOKIE_JSON
baha_cookie_daily.json -> BAHA_DAILY_COOKIE_JSON
baha_cookie_guild.json -> BAHA_GUILD_COOKIE_JSON
baha_cookie_ani.json   -> BAHA_ANIME_COOKIE_JSON
```

Paste the JSON file contents into GitHub Actions Secrets in your private workflow repository. Do not commit JSON files to GitHub.

If you downloaded the source code, you can also run:

```bash
python -m pip install DrissionPage
python tools/export_bahamut_cookies.py
```

### How Automatic Cookie Refresh Works

On the first setup, manually save `BAHA_COOKIE_JSON` in your private workflow repository Secrets.

When the workflow runs, the sign-in program may capture a newer Cookie and write it to a temporary runner file. `bahamut-secret-refresher` then writes that temporary file back to:

```text
BAHA_REFRESHED_COOKIE
BAHA_REFRESHED_DAILY_COOKIE
BAHA_REFRESHED_GUILD_COOKIE
```

The next workflow run should use `BAHA_REFRESHED_COOKIE`, `BAHA_REFRESHED_DAILY_COOKIE`, and `BAHA_REFRESHED_GUILD_COOKIE` first. If one becomes invalid, delete the invalid Secret, export a fresh Cookie JSON, and update the matching `BAHA_COOKIE_JSON`, `BAHA_DAILY_COOKIE_JSON`, or `BAHA_GUILD_COOKIE_JSON`.

Recommended layout:

```text
BAHA_COOKIE_JSON       manually exported full Cookie JSON
BAHA_REFRESHED_COOKIE  automatically updated one-line Cookie
BAHA_DAILY_COOKIE_JSON daily check-in Cookie JSON
BAHA_REFRESHED_DAILY_COOKIE  automatically updated one-line daily check-in Cookie
BAHA_GUILD_COOKIE_JSON manually exported full guild Cookie JSON
BAHA_REFRESHED_GUILD_COOKIE  automatically updated one-line guild Cookie
```

Do not overwrite full `BAHA_COOKIE_JSON` with a smaller one-line Cookie.

### Create A GitHub Token

Updating GitHub Actions Secrets requires a Fine-grained personal access token. Create it here:

```text
GitHub > Settings > Developer settings > Personal access tokens > Fine-grained tokens > Generate new token
```

Recommended settings:

```text
Repository access:
  Only selected repositories

Selected repository:
  Your private workflow repository

Repository permissions:
  Secrets: Read and write
  Metadata: Read-only
```

Save the token in the private workflow repository Secret:

```text
BAHA_SECRET_UPDATE_TOKEN
```

### Secret Update Command

`bahamut-secret-refresher` uses these environment variables:

| Name | Required | Description |
| --- | --- | --- |
| `SECRET_UPDATE_TOKEN` | Yes | Fine-grained token allowed to update repository Secrets. |
| `TARGET_REPOSITORY` | Yes | Target repository in `OWNER/REPO` format. |
| `SECRET_NAME` | Yes | Secret name to create or update. |
| `SECRET_FILE` | No | File containing the new Secret value. |
| `SECRET_VALUE` | No | Direct Secret value, used when `SECRET_FILE` is not set. |

Test with a harmless value first:

```bash
export SECRET_UPDATE_TOKEN="your fine-grained token"
export TARGET_REPOSITORY="OWNER/PRIVATE_WORKFLOW_REPO"
export SECRET_NAME="TEST_AUTO_UPDATED_SECRET"
export SECRET_VALUE="hello"
bahamut-secret-refresher
```

After the test Secret can be created, connect it to the real workflow.

### Limits

This tool cannot make Cookies valid forever. It only saves a refreshed value when the current login state is still accepted and the workflow captures a new Cookie.

It cannot handle:

- full re-login requirements
- CAPTCHA, two-factor verification, or Cloudflare challenges
- server-side session revocation
- expired or under-permissioned GitHub tokens

## 简体中文

这是一个公开工具包，提供两个命令：

```text
bahamut-cookie-exporter
bahamut-secret-refresher
```

`bahamut-cookie-exporter` 用来在本机打开 Chromium，让用户手动登录巴哈姆特后导出 Cookie JSON。  
`bahamut-secret-refresher` 用来在 GitHub Actions 里，把 workflow 捕获到的新 Cookie 写回 GitHub Actions Secret。

公开 repository 只应该放工具程序和教学文档。不要提交真实 Cookie、Token、密码、Cookie JSON 文件、浏览器 profile 或私人 workflow。

### 安装

如果直接使用这个公开工具：

```bash
python -m pip install "git+https://github.com/git-buster/bahamut-auto-signer.git[export]"
```

如果你 fork 或复制成自己的公开 repository，请把 `OWNER/REPO` 换成你的 repository：

```bash
python -m pip install "git+https://github.com/OWNER/REPO.git[export]"
```

### 导出 Cookie JSON

在自己的电脑执行：

```bash
bahamut-cookie-exporter
```

工具会打开 Chromium，依次前往：

```text
https://www.gamer.com.tw/
https://www.gamer.com.tw/dailySign.php
https://guild.gamer.com.tw/
https://ani.gamer.com.tw/
```

你需要在浏览器里正常登录。每个页面确认登录后，回到终端按 Enter，工具会输出：

```text
baha_cookie_www.json   -> BAHA_COOKIE_JSON
baha_cookie_daily.json -> BAHA_DAILY_COOKIE_JSON
baha_cookie_guild.json -> BAHA_GUILD_COOKIE_JSON
baha_cookie_ani.json   -> BAHA_ANIME_COOKIE_JSON
```

把 JSON 文件内容完整贴到私人 workflow repository 的 GitHub Actions Secrets。不要把 JSON 文件提交到 GitHub。

如果你下载了源码，也可以这样执行：

```bash
python -m pip install DrissionPage
python tools/export_bahamut_cookies.py
```

### 自动更新 Cookie 的原理

第一次使用时，你手动把 `BAHA_COOKIE_JSON` 放到私人 workflow repository 的 Secrets。

workflow 执行签到时，如果程序捕获到新的 Cookie，会把它写到 runner 的临时文件。接着 `bahamut-secret-refresher` 会把这个临时文件内容更新到：

```text
BAHA_REFRESHED_COOKIE
BAHA_REFRESHED_DAILY_COOKIE
BAHA_REFRESHED_GUILD_COOKIE
```

下一次 workflow 会优先使用 `BAHA_REFRESHED_COOKIE`、`BAHA_REFRESHED_DAILY_COOKIE` 和 `BAHA_REFRESHED_GUILD_COOKIE`。如果其中一个失效，删除失效的 Secret，重新导出 Cookie JSON，更新对应的 `BAHA_COOKIE_JSON`、`BAHA_DAILY_COOKIE_JSON` 或 `BAHA_GUILD_COOKIE_JSON`。

建议保留这种结构：

```text
BAHA_COOKIE_JSON       手动导出的完整 Cookie JSON
BAHA_REFRESHED_COOKIE  workflow 自动更新的一行 Cookie
BAHA_DAILY_COOKIE_JSON 每日签到专用 Cookie JSON
BAHA_REFRESHED_DAILY_COOKIE  workflow 自动更新的一行每日签到 Cookie
BAHA_GUILD_COOKIE_JSON 手动导出的完整公会 Cookie JSON
BAHA_REFRESHED_GUILD_COOKIE  workflow 自动更新的一行公会 Cookie
```

不要直接用一行 Cookie 覆盖完整的 `BAHA_COOKIE_JSON`。

### 创建 GitHub Token

自动更新 GitHub Actions Secret 需要一个 Fine-grained personal access token。创建路径：

```text
GitHub > Settings > Developer settings > Personal access tokens > Fine-grained tokens > Generate new token
```

建议设置：

```text
Repository access:
  Only selected repositories

Selected repository:
  你的私人 workflow repository

Repository permissions:
  Secrets: Read and write
  Metadata: Read-only
```

把 Token 保存到私人 workflow repository 的 Secret：

```text
BAHA_SECRET_UPDATE_TOKEN
```

### Secret 更新命令

`bahamut-secret-refresher` 需要这些环境变量：

| 名称 | 必填 | 说明 |
| --- | --- | --- |
| `SECRET_UPDATE_TOKEN` | 是 | 可以更新 repository Secrets 的 Fine-grained Token。 |
| `TARGET_REPOSITORY` | 是 | 目标 repository，格式为 `OWNER/REPO`。 |
| `SECRET_NAME` | 是 | 要创建或更新的 Secret 名称。 |
| `SECRET_FILE` | 否 | 存放新 Secret 值的文件。 |
| `SECRET_VALUE` | 否 | 直接提供的新 Secret 值；未设置 `SECRET_FILE` 时使用。 |

先用无害值测试：

```bash
export SECRET_UPDATE_TOKEN="your fine-grained token"
export TARGET_REPOSITORY="OWNER/PRIVATE_WORKFLOW_REPO"
export SECRET_NAME="TEST_AUTO_UPDATED_SECRET"
export SECRET_VALUE="hello"
bahamut-secret-refresher
```

确认测试 Secret 可以创建后，再接入真实 workflow。

### 限制

这个工具不能保证 Cookie 永久有效。它只能在当前登录状态仍被网站接受、且 workflow 捕获到新 Cookie 时，帮你把新值保存起来。

它不能处理：

- 网站要求完整重新登录
- CAPTCHA、二次验证或 Cloudflare 验证
- 服务器端主动撤销 session
- GitHub Token 过期或权限不足
