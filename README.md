# Bahamut Secret Refresher Helper

## 繁體中文

這個工具可以在 GitHub Actions workflow 裡，把一個新的值寫回指定的 GitHub Actions Secret。它適合用在 Cookie 型自動化：當你的簽到流程成功捕獲到更新後的 Cookie，就可以把它保存成 Secret，讓下一次 workflow 優先使用新的 Cookie。

公開倉庫只應該放這個通用工具與說明文件。請不要提交真實 Cookie、Token、密碼、瀏覽器 Cookie JSON、瀏覽器 profile，或私人 workflow 設定。

### 功能

`scripts/update_actions_secret_with_gh.py` 會從暫存檔或環境變數讀取 Secret 值，然後透過 GitHub CLI 更新指定 repository 的 Actions Secret。

也可以安裝後直接執行：

```bash
python -m pip install git+https://github.com/OWNER/REPO.git
bahamut-secret-refresher
```

它會：

- 拒絕寫入空值
- 在 GitHub Actions log 裡遮罩 Secret 值
- 透過標準輸入把值傳給 `gh secret set`
- 不主動列印 Cookie 或 Token 內容

### 限制

這個工具不能讓網站 session 永久有效。它只能在目前 session 仍被網站接受、且流程捕獲到新 Cookie 時，把新值保存起來。

它不能處理：

- 網站要求完整重新登入
- CAPTCHA、二次驗證、Cloudflare 驗證
- 伺服器端主動撤銷 session
- GitHub Token 過期或權限不足

### GitHub Token 權限

建議建立 Fine-grained personal access token：

```text
GitHub > Settings > Developer settings > Personal access tokens > Fine-grained tokens > Generate new token
```

建議設定：

```text
Repository access:
  Only selected repositories

Selected repository:
  儲存 Actions Secrets 的私人 workflow repository

Repository permissions:
  Secrets: Read and write
  Metadata: Read-only
```

把 Token 保存到私人 workflow repository 的 Secret：

```text
BAHA_SECRET_UPDATE_TOKEN
```

### 腳本參數

| 名稱 | 必填 | 說明 |
| --- | --- | --- |
| `SECRET_UPDATE_TOKEN` | 是 | 具備 repository Secrets 寫入權限的 Fine-grained Token。 |
| `TARGET_REPOSITORY` | 是 | 目標 repository，格式為 `OWNER/REPO`。 |
| `SECRET_NAME` | 是 | 要建立或更新的 Actions Secret 名稱。 |
| `SECRET_FILE` | 否 | 存放新 Secret 值的檔案。 |
| `SECRET_VALUE` | 否 | 直接提供的新 Secret 值；未設定 `SECRET_FILE` 時使用。 |

Cookie refresh workflow 建議使用 `SECRET_FILE`，把捕獲到的新 Cookie 放在 runner 暫存檔中，避免提交到 repository。

### 本機測試

請先用無害值測試，不要一開始就使用真實 Cookie。

PowerShell：

```powershell
$env:SECRET_UPDATE_TOKEN = "your fine-grained token"
$env:TARGET_REPOSITORY = "OWNER/REPO"
$env:SECRET_NAME = "TEST_AUTO_UPDATED_SECRET"
$env:SECRET_VALUE = "hello"
python .\scripts\update_actions_secret_with_gh.py
```

Bash：

```bash
export SECRET_UPDATE_TOKEN="your fine-grained token"
export TARGET_REPOSITORY="OWNER/REPO"
export SECRET_NAME="TEST_AUTO_UPDATED_SECRET"
export SECRET_VALUE="hello"
python scripts/update_actions_secret_with_gh.py
```

測試後到這裡確認：

```text
Repository Settings > Secrets and variables > Actions > Secrets
```

### 建議 Cookie Secret 結構

保留手動匯出的完整 Cookie JSON 作為恢復來源，另存一個 workflow 自動更新的一行 Cookie：

```text
BAHA_COOKIE_JSON       手動匯出的完整 Cookie JSON
BAHA_REFRESHED_COOKIE  workflow 自動更新的一行 Cookie
```

下次運行時優先使用 `BAHA_REFRESHED_COOKIE`。如果它失效，刪除這個 Secret，重新匯出 Cookie JSON 並更新 `BAHA_COOKIE_JSON`。

這樣可以避免把完整 Cookie JSON 覆蓋成不完整的一行 Cookie。

## English

This helper updates a GitHub Actions Secret from inside a workflow. It is useful for Cookie-based automation: when your workflow captures a refreshed Cookie, it can save that value as a Secret so the next run can use it first.

The public repository should contain only this reusable helper and documentation. Do not commit real Cookies, tokens, passwords, exported browser Cookie JSON files, browser profiles, or private workflow configuration.

### Features

`scripts/update_actions_secret_with_gh.py` reads a secret value from a temporary file or environment variable, then uses the GitHub CLI to update a repository Actions Secret.

After installation, you can also run:

```bash
python -m pip install git+https://github.com/OWNER/REPO.git
bahamut-secret-refresher
```

It:

- refuses to write an empty value
- masks the value in GitHub Actions logs
- passes the value to `gh secret set` through standard input
- does not print Cookie or token contents

### Limits

This helper cannot make a website session valid forever. It only saves a refreshed value when the current session is still accepted and the workflow captures a new Cookie.

It cannot handle:

- a required full login
- CAPTCHA, two-factor verification, or Cloudflare challenges
- server-side session revocation
- an expired or under-permissioned GitHub token

### GitHub Token Permissions

Create a Fine-grained personal access token:

```text
GitHub > Settings > Developer settings > Personal access tokens > Fine-grained tokens > Generate new token
```

Recommended settings:

```text
Repository access:
  Only selected repositories

Selected repository:
  The private workflow repository that stores Actions Secrets

Repository permissions:
  Secrets: Read and write
  Metadata: Read-only
```

Save the token in the private workflow repository as:

```text
BAHA_SECRET_UPDATE_TOKEN
```

### Script Settings

| Name | Required | Description |
| --- | --- | --- |
| `SECRET_UPDATE_TOKEN` | Yes | Fine-grained token with repository Secrets write permission. |
| `TARGET_REPOSITORY` | Yes | Target repository in `OWNER/REPO` format. |
| `SECRET_NAME` | Yes | Name of the Actions Secret to create or update. |
| `SECRET_FILE` | No | File containing the new Secret value. |
| `SECRET_VALUE` | No | Direct value used when `SECRET_FILE` is not set. |

For Cookie refresh workflows, `SECRET_FILE` is recommended because the refreshed Cookie can be stored in a temporary runner file and never committed.

### Local Test

Test with a harmless value before using a real Cookie.

PowerShell:

```powershell
$env:SECRET_UPDATE_TOKEN = "your fine-grained token"
$env:TARGET_REPOSITORY = "OWNER/REPO"
$env:SECRET_NAME = "TEST_AUTO_UPDATED_SECRET"
$env:SECRET_VALUE = "hello"
python .\scripts\update_actions_secret_with_gh.py
```

Bash:

```bash
export SECRET_UPDATE_TOKEN="your fine-grained token"
export TARGET_REPOSITORY="OWNER/REPO"
export SECRET_NAME="TEST_AUTO_UPDATED_SECRET"
export SECRET_VALUE="hello"
python scripts/update_actions_secret_with_gh.py
```

Then check:

```text
Repository Settings > Secrets and variables > Actions > Secrets
```

### Recommended Cookie Secret Layout

Keep your manually exported full Cookie JSON as the recovery source, and save the automatically refreshed one-line Cookie into a separate Secret:

```text
BAHA_COOKIE_JSON       manually exported full Cookie JSON
BAHA_REFRESHED_COOKIE  automatically updated one-line Cookie
```

On the next run, use `BAHA_REFRESHED_COOKIE` first. If it becomes invalid, delete that Secret, export a fresh Cookie JSON, and update `BAHA_COOKIE_JSON`.

This avoids overwriting a complete browser Cookie JSON with a smaller one-line Cookie value.

## 简体中文

这个工具可以在 GitHub Actions workflow 里，把一个新的值写回指定的 GitHub Actions Secret。它适合用于 Cookie 型自动化：当签到流程成功捕获到更新后的 Cookie，就可以把它保存成 Secret，让下一次 workflow 优先使用新的 Cookie。

公开仓库只应该放这个通用工具和说明文档。请不要提交真实 Cookie、Token、密码、浏览器 Cookie JSON、浏览器 profile，或私人 workflow 配置。

### 功能

`scripts/update_actions_secret_with_gh.py` 会从临时文件或环境变量读取 Secret 值，然后通过 GitHub CLI 更新指定 repository 的 Actions Secret。

安装后也可以直接执行：

```bash
python -m pip install git+https://github.com/OWNER/REPO.git
bahamut-secret-refresher
```

它会：

- 拒绝写入空值
- 在 GitHub Actions log 里遮罩 Secret 值
- 通过标准输入把值传给 `gh secret set`
- 不主动打印 Cookie 或 Token 内容

### 限制

这个工具不能让网站 session 永久有效。它只能在当前 session 仍被网站接受、且流程捕获到新 Cookie 时，把新值保存起来。

它不能处理：

- 网站要求完整重新登录
- CAPTCHA、二次验证、Cloudflare 验证
- 服务器端主动撤销 session
- GitHub Token 过期或权限不足

### GitHub Token 权限

建议创建 Fine-grained personal access token：

```text
GitHub > Settings > Developer settings > Personal access tokens > Fine-grained tokens > Generate new token
```

建议设置：

```text
Repository access:
  Only selected repositories

Selected repository:
  保存 Actions Secrets 的私人 workflow repository

Repository permissions:
  Secrets: Read and write
  Metadata: Read-only
```

把 Token 保存到私人 workflow repository 的 Secret：

```text
BAHA_SECRET_UPDATE_TOKEN
```

### 脚本参数

| 名称 | 必填 | 说明 |
| --- | --- | --- |
| `SECRET_UPDATE_TOKEN` | 是 | 具备 repository Secrets 写入权限的 Fine-grained Token。 |
| `TARGET_REPOSITORY` | 是 | 目标 repository，格式为 `OWNER/REPO`。 |
| `SECRET_NAME` | 是 | 要创建或更新的 Actions Secret 名称。 |
| `SECRET_FILE` | 否 | 存放新 Secret 值的文件。 |
| `SECRET_VALUE` | 否 | 直接提供的新 Secret 值；未设置 `SECRET_FILE` 时使用。 |

Cookie refresh workflow 建议使用 `SECRET_FILE`，把捕获到的新 Cookie 放在 runner 临时文件中，避免提交到 repository。

### 本地测试

请先用无害值测试，不要一开始就使用真实 Cookie。

PowerShell：

```powershell
$env:SECRET_UPDATE_TOKEN = "your fine-grained token"
$env:TARGET_REPOSITORY = "OWNER/REPO"
$env:SECRET_NAME = "TEST_AUTO_UPDATED_SECRET"
$env:SECRET_VALUE = "hello"
python .\scripts\update_actions_secret_with_gh.py
```

Bash：

```bash
export SECRET_UPDATE_TOKEN="your fine-grained token"
export TARGET_REPOSITORY="OWNER/REPO"
export SECRET_NAME="TEST_AUTO_UPDATED_SECRET"
export SECRET_VALUE="hello"
python scripts/update_actions_secret_with_gh.py
```

测试后到这里确认：

```text
Repository Settings > Secrets and variables > Actions > Secrets
```

### 建议 Cookie Secret 结构

保留手动导出的完整 Cookie JSON 作为恢复来源，另存一个 workflow 自动更新的一行 Cookie：

```text
BAHA_COOKIE_JSON       手动导出的完整 Cookie JSON
BAHA_REFRESHED_COOKIE  workflow 自动更新的一行 Cookie
```

下次运行时优先使用 `BAHA_REFRESHED_COOKIE`。如果它失效，删除这个 Secret，重新导出 Cookie JSON 并更新 `BAHA_COOKIE_JSON`。

这样可以避免把完整 Cookie JSON 覆盖成不完整的一行 Cookie。
