# Bahamut Auto Signer

Bahamut Auto Signer is a Python command-line tool for running Bahamut daily
check-ins locally or from GitHub Actions.

It supports daily sign-in, guild sign-in, optional Ani-Gamer daily quiz attempts,
GitHub Actions summaries, and optional Discord / Telegram notifications.

Languages: [繁體中文](#繁體中文) | [简体中文](#简体中文) | [English](#english)

## 繁體中文

### 功能

- 巴哈姆特每日簽到。
- 公會簽到，預設開啟。
- 動畫瘋每日答題，預設關閉。
- 廣告加倍入口偵測與手動提醒。
- GitHub Actions Summary 輸出。
- 可選 Discord / Telegram 通知。
- 支援一般 Cookie 字串與瀏覽器匯出的 Cookie JSON。
- 同一個公開包也提供 `bahamut-cookie-exporter` 與 `bahamut-secret-refresher`。

廣告加倍只會偵測與提醒，不會自動觀看廣告、繞過驗證或偽造廣告完成請求。

### 安裝

從 GitHub 安裝：

```bash
python -m pip install git+https://github.com/git-buster/bahamut-auto-signer.git
```

從原始碼安裝：

```bash
git clone https://github.com/git-buster/bahamut-auto-signer.git
cd bahamut-auto-signer
python -m pip install .
```

### 本機使用

設定 Cookie 後執行：

```bash
export BAHA_COOKIE_JSON='貼上 Cookie JSON'
baha-auto-signer
```

Windows PowerShell：

```powershell
$env:BAHA_COOKIE_JSON = '貼上 Cookie JSON'
baha-auto-signer
```

如果只想先測試公會簽到，也建議同時設定公會 Cookie：

```powershell
$env:BAHA_GUILD_COOKIE_JSON = '貼上 guild.gamer.com.tw 的 Cookie JSON'
```

### GitHub Actions 使用

建議把 GitHub Actions 放在 private repository，因為 Secrets 裡會保存你的 Cookie。

1. 在 GitHub 建立一個 private repository。
2. 建立 `.github/workflows/bahamut-signin.yml`。
3. 貼上下面的 workflow。
4. 到 **Settings > Secrets and variables > Actions** 設定 Secrets。
5. 到 **Actions > Bahamut Sign In > Run workflow** 手動測試一次。

```yaml
name: Bahamut Sign In

on:
  workflow_dispatch:
  schedule:
    - cron: "0 1 * * *"

permissions:
  contents: read

jobs:
  signin:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    env:
      BAHA_COOKIE: ${{ secrets.BAHA_COOKIE }}
      BAHA_COOKIE_JSON: ${{ secrets.BAHA_COOKIE_JSON }}
      BAHA_GUILD_COOKIE: ${{ secrets.BAHA_GUILD_COOKIE }}
      BAHA_GUILD_COOKIE_JSON: ${{ secrets.BAHA_GUILD_COOKIE_JSON }}
      BAHA_ANIME_COOKIE: ${{ secrets.BAHA_ANIME_COOKIE }}
      BAHA_ANIME_COOKIE_JSON: ${{ secrets.BAHA_ANIME_COOKIE_JSON }}
      ENABLE_GUILD_CHECKIN: ${{ vars.ENABLE_GUILD_CHECKIN || 'true' }}
      ENABLE_ANIME_QUIZ: ${{ vars.ENABLE_ANIME_QUIZ || 'false' }}
      GUILD_CHECKIN_DELAY_SECONDS: ${{ vars.GUILD_CHECKIN_DELAY_SECONDS || '1.0' }}
      DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK_URL }}
      TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
      TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}

    steps:
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install baha-auto-signer
        run: python -m pip install git+https://github.com/git-buster/bahamut-auto-signer.git

      - name: Run Bahamut check-in
        run: baha-auto-signer
```

`0 1 * * *` 是 UTC 01:00，對應台灣、香港、新加坡每天 09:00。

### 匯出 Cookie JSON

推薦使用 Cookie JSON，而不是只從 Network 複製一行 Cookie。JSON 會保留 domain、path、expires、httpOnly、secure 等欄位，對公會和動畫瘋比較穩定。

先安裝匯出工具需要的套件：

```bash
python -m pip install DrissionPage
```

在已安裝或已 clone 的專案目錄執行：

```bash
python tools/export_bahamut_cookies.py
```

腳本會開啟 Chromium，依序打開：

```text
https://www.gamer.com.tw/
https://www.gamer.com.tw/  （daily 階段請先打開右上角每日簽到入口）
https://guild.gamer.com.tw/
https://ani.gamer.com.tw/
```

每個頁面確認已登入後，回到終端按 Enter。daily 階段請先在巴哈主站右上角打開每日簽到入口，再按 Enter。完成後會產生：

```text
baha_cookie_www.json   -> BAHA_COOKIE_JSON
baha_cookie_daily.json -> BAHA_DAILY_COOKIE_JSON
baha_cookie_guild.json -> BAHA_GUILD_COOKIE_JSON
baha_cookie_ani.json   -> BAHA_ANIME_COOKIE_JSON
```

把 JSON 檔案內容貼到 GitHub Actions Secrets。不要把 Cookie JSON 提交到 GitHub。

### Secrets

至少設定其中一個：

| 名稱 | 說明 |
| --- | --- |
| `BAHA_COOKIE_JSON` | 從主站登入狀態匯出的完整 Cookie JSON，建議使用。 |
| `BAHA_COOKIE` | 從瀏覽器 Network Request Headers 複製的一行 Cookie，作為相容方案。 |
| `BAHA_DAILY_COOKIE_JSON` | 從每日簽到頁匯出的完整 Cookie JSON。每日簽到出現 `NO_LOGIN` 時建議使用。 |
| `BAHA_DAILY_COOKIE` | 每日簽到專用的一行 Cookie。 |

可選：

| 名稱 | 說明 |
| --- | --- |
| `BAHA_GUILD_COOKIE_JSON` | 從 `guild.gamer.com.tw` 匯出的 Cookie JSON，建議公會簽到使用。 |
| `BAHA_GUILD_COOKIE` | 公會網域專用的一行 Cookie。 |
| `BAHA_ANIME_COOKIE_JSON` | 從 `ani.gamer.com.tw` 匯出的 Cookie JSON，開啟動畫瘋答題時建議使用。 |
| `BAHA_ANIME_COOKIE` | 動畫瘋網域專用的一行 Cookie。 |
| `DISCORD_WEBHOOK_URL` | 將結果發送到 Discord webhook。 |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot token。 |
| `TELEGRAM_CHAT_ID` | Telegram chat id。 |

### Variables

可在 GitHub Actions Variables 設定：

| 名稱 | 預設 | 說明 |
| --- | --- | --- |
| `ENABLE_GUILD_CHECKIN` | `true` | 是否執行公會簽到。 |
| `ENABLE_ANIME_QUIZ` | `false` | 是否嘗試動畫瘋每日答題。 |
| `GUILD_CHECKIN_DELAY_SECONDS` | `1.0` | 每個公會簽到之間等待幾秒；如果公會容易要求重新登入，可調到 `2` 或 `3`。 |

### 結果與排錯

- 每日簽到會送出簽到請求，並再查一次狀態，避免只看 API 回傳造成誤判。
- 公會簽到會辨識 `簽到成功`、`已簽到`、`獲得`、`GP`、`經驗`、`巴幣` 等成功文字。
- `請先登入`、`重新登入`、`login` 等會視為失敗。
- 只要啟用的項目有任一失敗，GitHub Action 會回傳失敗狀態。
- 如果公會簽到提示要重新登入，優先重新匯出並更新 `BAHA_GUILD_COOKIE_JSON`。
- 如果 GitHub-hosted runner 經常觸發風控，可以考慮使用 self-hosted runner。

Cookie JSON 比單行 Cookie 更完整，但不能保證永遠有效。若巴哈伺服器端撤銷 session、Cloudflare 重新驗證、或 runner IP 被風控，仍可能需要重新登入並匯出。

## 简体中文

### 功能

- 巴哈姆特每日签到。
- 公会签到，默认开启。
- 动画疯每日答题，默认关闭。
- 广告加倍入口检测与手动提醒。
- GitHub Actions Summary 输出。
- 可选 Discord / Telegram 通知。
- 支持普通 Cookie 字符串和浏览器导出的 Cookie JSON。
- 同一个公开包也提供 `bahamut-cookie-exporter` 和 `bahamut-secret-refresher`。

广告加倍只会检测和提醒，不会自动观看广告、绕过验证或伪造广告完成请求。

### 安装

从 GitHub 安装：

```bash
python -m pip install git+https://github.com/git-buster/bahamut-auto-signer.git
```

从源码安装：

```bash
git clone https://github.com/git-buster/bahamut-auto-signer.git
cd bahamut-auto-signer
python -m pip install .
```

### 本地使用

设置 Cookie 后执行：

```bash
export BAHA_COOKIE_JSON='贴上 Cookie JSON'
baha-auto-signer
```

Windows PowerShell：

```powershell
$env:BAHA_COOKIE_JSON = '贴上 Cookie JSON'
baha-auto-signer
```

如果想测试公会签到，也建议同时设置公会 Cookie：

```powershell
$env:BAHA_GUILD_COOKIE_JSON = '贴上 guild.gamer.com.tw 的 Cookie JSON'
```

### GitHub Actions 使用

建议把 GitHub Actions 放在 private repository，因为 Secrets 里会保存你的 Cookie。

1. 在 GitHub 创建一个 private repository。
2. 创建 `.github/workflows/bahamut-signin.yml`。
3. 粘贴下面的 workflow。
4. 到 **Settings > Secrets and variables > Actions** 设置 Secrets。
5. 到 **Actions > Bahamut Sign In > Run workflow** 手动测试一次。

```yaml
name: Bahamut Sign In

on:
  workflow_dispatch:
  schedule:
    - cron: "0 1 * * *"

permissions:
  contents: read

jobs:
  signin:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    env:
      BAHA_COOKIE: ${{ secrets.BAHA_COOKIE }}
      BAHA_COOKIE_JSON: ${{ secrets.BAHA_COOKIE_JSON }}
      BAHA_GUILD_COOKIE: ${{ secrets.BAHA_GUILD_COOKIE }}
      BAHA_GUILD_COOKIE_JSON: ${{ secrets.BAHA_GUILD_COOKIE_JSON }}
      BAHA_ANIME_COOKIE: ${{ secrets.BAHA_ANIME_COOKIE }}
      BAHA_ANIME_COOKIE_JSON: ${{ secrets.BAHA_ANIME_COOKIE_JSON }}
      ENABLE_GUILD_CHECKIN: ${{ vars.ENABLE_GUILD_CHECKIN || 'true' }}
      ENABLE_ANIME_QUIZ: ${{ vars.ENABLE_ANIME_QUIZ || 'false' }}
      GUILD_CHECKIN_DELAY_SECONDS: ${{ vars.GUILD_CHECKIN_DELAY_SECONDS || '1.0' }}
      DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK_URL }}
      TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
      TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}

    steps:
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install baha-auto-signer
        run: python -m pip install git+https://github.com/git-buster/bahamut-auto-signer.git

      - name: Run Bahamut check-in
        run: baha-auto-signer
```

`0 1 * * *` 是 UTC 01:00，对应台湾、香港、新加坡每天 09:00。

### 导出 Cookie JSON

推荐使用 Cookie JSON，而不是只从 Network 复制一行 Cookie。JSON 会保留 domain、path、expires、httpOnly、secure 等字段，对公会和动画疯比较稳定。

先安装导出工具需要的套件：

```bash
python -m pip install DrissionPage
```

在已安装或已 clone 的项目目录执行：

```bash
python tools/export_bahamut_cookies.py
```

脚本会打开 Chromium，依次打开：

```text
https://www.gamer.com.tw/
https://www.gamer.com.tw/  （daily 阶段请先打开右上角每日签到入口）
https://guild.gamer.com.tw/
https://ani.gamer.com.tw/
```

每个页面确认已登录后，回到终端按 Enter。daily 阶段请先在巴哈主站右上角打开每日签到入口，再按 Enter。完成后会生成：

```text
baha_cookie_www.json   -> BAHA_COOKIE_JSON
baha_cookie_daily.json -> BAHA_DAILY_COOKIE_JSON
baha_cookie_guild.json -> BAHA_GUILD_COOKIE_JSON
baha_cookie_ani.json   -> BAHA_ANIME_COOKIE_JSON
```

把 JSON 文件内容贴到 GitHub Actions Secrets。不要把 Cookie JSON 提交到 GitHub。

### Secrets

至少设置其中一个：

| 名称 | 说明 |
| --- | --- |
| `BAHA_COOKIE_JSON` | 从主站登录状态导出的完整 Cookie JSON，建议使用。 |
| `BAHA_COOKIE` | 从浏览器 Network Request Headers 复制的一行 Cookie，作为兼容方案。 |
| `BAHA_DAILY_COOKIE_JSON` | 从每日签到页导出的完整 Cookie JSON。每日签到出现 `NO_LOGIN` 时建议使用。 |
| `BAHA_DAILY_COOKIE` | 每日签到专用的一行 Cookie。 |

可选：

| 名称 | 说明 |
| --- | --- |
| `BAHA_GUILD_COOKIE_JSON` | 从 `guild.gamer.com.tw` 导出的 Cookie JSON，建议公会签到使用。 |
| `BAHA_GUILD_COOKIE` | 公会域名专用的一行 Cookie。 |
| `BAHA_ANIME_COOKIE_JSON` | 从 `ani.gamer.com.tw` 导出的 Cookie JSON，开启动画疯答题时建议使用。 |
| `BAHA_ANIME_COOKIE` | 动画疯域名专用的一行 Cookie。 |
| `DISCORD_WEBHOOK_URL` | 将结果发送到 Discord webhook。 |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot token。 |
| `TELEGRAM_CHAT_ID` | Telegram chat id。 |

### Variables

可在 GitHub Actions Variables 设置：

| 名称 | 默认 | 说明 |
| --- | --- | --- |
| `ENABLE_GUILD_CHECKIN` | `true` | 是否执行公会签到。 |
| `ENABLE_ANIME_QUIZ` | `false` | 是否尝试动画疯每日答题。 |
| `GUILD_CHECKIN_DELAY_SECONDS` | `1.0` | 每个公会签到之间等待几秒；如果公会容易要求重新登录，可以调到 `2` 或 `3`。 |

### 结果与排错

- 每日签到会送出签到请求，并再查一次状态，避免只看 API 返回造成误判。
- 公会签到会识别 `签到成功`、`已签到`、`获得`、`GP`、`经验`、`巴币` 等成功文字。
- `请先登录`、`重新登录`、`login` 等会视为失败。
- 只要启用的项目有任一失败，GitHub Action 会返回失败状态。
- 如果公会签到提示要重新登录，优先重新导出并更新 `BAHA_GUILD_COOKIE_JSON`。
- 如果 GitHub-hosted runner 经常触发风控，可以考虑使用 self-hosted runner。

Cookie JSON 比单行 Cookie 更完整，但不能保证一直有效。如果巴哈服务器端撤销 session、Cloudflare 重新验证、或 runner IP 被风控，仍可能需要重新登录并导出。

## English

### Features

- Bahamut daily check-in.
- Guild check-in, enabled by default.
- Ani-Gamer daily quiz attempt, disabled by default.
- Ad bonus entry detection with a manual reminder.
- GitHub Actions Summary output.
- Optional Discord / Telegram notifications.
- Supports both plain Cookie headers and browser-exported Cookie JSON.
- The same public package also provides `bahamut-cookie-exporter` and `bahamut-secret-refresher`.

Ad bonus handling is limited to detection and reminders. This tool does not
watch ads, bypass ad verification, or fake ad-completion requests.

### Installation

Install from GitHub:

```bash
python -m pip install git+https://github.com/git-buster/bahamut-auto-signer.git
```

Install from source:

```bash
git clone https://github.com/git-buster/bahamut-auto-signer.git
cd bahamut-auto-signer
python -m pip install .
```

### Local Usage

Set a Cookie secret and run:

```bash
export BAHA_COOKIE_JSON='paste Cookie JSON here'
baha-auto-signer
```

Windows PowerShell:

```powershell
$env:BAHA_COOKIE_JSON = 'paste Cookie JSON here'
baha-auto-signer
```

For guild check-in testing, also set the guild-domain Cookie JSON:

```powershell
$env:BAHA_GUILD_COOKIE_JSON = 'paste guild.gamer.com.tw Cookie JSON here'
```

### GitHub Actions Usage

Use a private GitHub repository for the workflow because GitHub Actions Secrets
will contain your Cookie.

1. Create a private GitHub repository.
2. Create `.github/workflows/bahamut-signin.yml`.
3. Paste the workflow below.
4. Configure Secrets in **Settings > Secrets and variables > Actions**.
5. Open **Actions > Bahamut Sign In > Run workflow** and run it once manually.

```yaml
name: Bahamut Sign In

on:
  workflow_dispatch:
  schedule:
    - cron: "0 1 * * *"

permissions:
  contents: read

jobs:
  signin:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    env:
      BAHA_COOKIE: ${{ secrets.BAHA_COOKIE }}
      BAHA_COOKIE_JSON: ${{ secrets.BAHA_COOKIE_JSON }}
      BAHA_GUILD_COOKIE: ${{ secrets.BAHA_GUILD_COOKIE }}
      BAHA_GUILD_COOKIE_JSON: ${{ secrets.BAHA_GUILD_COOKIE_JSON }}
      BAHA_ANIME_COOKIE: ${{ secrets.BAHA_ANIME_COOKIE }}
      BAHA_ANIME_COOKIE_JSON: ${{ secrets.BAHA_ANIME_COOKIE_JSON }}
      ENABLE_GUILD_CHECKIN: ${{ vars.ENABLE_GUILD_CHECKIN || 'true' }}
      ENABLE_ANIME_QUIZ: ${{ vars.ENABLE_ANIME_QUIZ || 'false' }}
      GUILD_CHECKIN_DELAY_SECONDS: ${{ vars.GUILD_CHECKIN_DELAY_SECONDS || '1.0' }}
      DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK_URL }}
      TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
      TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}

    steps:
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install baha-auto-signer
        run: python -m pip install git+https://github.com/git-buster/bahamut-auto-signer.git

      - name: Run Bahamut check-in
        run: baha-auto-signer
```

The cron expression `0 1 * * *` runs at 01:00 UTC, which is 09:00 in Taiwan,
Hong Kong, and Singapore.

### Export Cookie JSON

Cookie JSON is recommended over a one-line Cookie copied from Network. JSON
keeps fields such as domain, path, expires, httpOnly, and secure, which is more
reliable for guild and Ani-Gamer requests.

Install the browser export dependency:

```bash
python -m pip install DrissionPage
```

Run this from an installed or cloned project directory:

```bash
python tools/export_bahamut_cookies.py
```

The script opens Chromium and visits:

```text
https://www.gamer.com.tw/
https://www.gamer.com.tw/  (during the daily step, open the top-right daily sign-in entry first)
https://guild.gamer.com.tw/
https://ani.gamer.com.tw/
```

After each page is logged in, return to the terminal and press Enter. During the daily step, open the top-right daily sign-in entry on the Bahamut main site before pressing Enter. It writes:

```text
baha_cookie_www.json   -> BAHA_COOKIE_JSON
baha_cookie_daily.json -> BAHA_DAILY_COOKIE_JSON
baha_cookie_guild.json -> BAHA_GUILD_COOKIE_JSON
baha_cookie_ani.json   -> BAHA_ANIME_COOKIE_JSON
```

Paste the JSON file contents into GitHub Actions Secrets. Do not commit Cookie
JSON files to GitHub.

### Secrets

Set at least one:

| Name | Description |
| --- | --- |
| `BAHA_COOKIE_JSON` | Full Cookie JSON exported from a logged-in main site session. Recommended. |
| `BAHA_COOKIE` | One-line Cookie copied from browser Network Request Headers. Backward compatible. |
| `BAHA_DAILY_COOKIE_JSON` | Full Cookie JSON exported from the daily check-in page. Recommended when daily check-in returns `NO_LOGIN`. |
| `BAHA_DAILY_COOKIE` | One-line Cookie dedicated to daily check-in. |

Optional:

| Name | Description |
| --- | --- |
| `BAHA_GUILD_COOKIE_JSON` | Cookie JSON exported from `guild.gamer.com.tw`. Recommended for guild check-in. |
| `BAHA_GUILD_COOKIE` | One-line guild-domain Cookie. |
| `BAHA_ANIME_COOKIE_JSON` | Cookie JSON exported from `ani.gamer.com.tw`. Recommended when Ani-Gamer quiz is enabled. |
| `BAHA_ANIME_COOKIE` | One-line Ani-Gamer-domain Cookie. |
| `DISCORD_WEBHOOK_URL` | Sends the result summary to a Discord webhook. |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot token. |
| `TELEGRAM_CHAT_ID` | Telegram chat id. |

### Variables

Set these as GitHub Actions Variables:

| Name | Default | Description |
| --- | --- | --- |
| `ENABLE_GUILD_CHECKIN` | `true` | Whether to run guild check-in. |
| `ENABLE_ANIME_QUIZ` | `false` | Whether to try the Ani-Gamer daily quiz. |
| `GUILD_CHECKIN_DELAY_SECONDS` | `1.0` | Seconds to wait between guild check-ins; try `2` or `3` if guild requests are sensitive. |

### Results And Troubleshooting

- Daily check-in sends the check-in request and then verifies completion with a status check.
- Guild check-in recognizes success text such as `簽到成功`, `已簽到`, `獲得`, `GP`, `經驗`, and `巴幣`.
- Login-required text such as `請先登入`, `重新登入`, and `login` is treated as failure.
- If any enabled task fails, the GitHub Action exits with a failure status.
- If guild check-in asks you to log in again, refresh `BAHA_GUILD_COOKIE_JSON` first.
- If GitHub-hosted runners frequently trigger risk checks, consider a self-hosted runner.

Cookie JSON is more complete than a one-line Cookie, but it still cannot last
forever. If Bahamut invalidates the server-side session, Cloudflare asks for a
new challenge, or the runner IP is flagged, you may need to log in again and
export fresh Cookie JSON.
