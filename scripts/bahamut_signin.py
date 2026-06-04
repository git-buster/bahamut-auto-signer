from __future__ import annotations

import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from typing import Any

import requests


BASE_WEB_URL = "https://www.gamer.com.tw"
BASE_API_URL = "https://api.gamer.com.tw"
BASE_GUILD_URL = "https://guild.gamer.com.tw"
BASE_ANI_URL = "https://ani.gamer.com.tw"
COOKIE_REFRESH_FILE_ENV = "BAHA_REFRESHED_COOKIE_PATH"
DAILY_COOKIE_REFRESH_FILE_ENV = "BAHA_REFRESHED_DAILY_COOKIE_PATH"
GUILD_COOKIE_REFRESH_FILE_ENV = "BAHA_REFRESHED_GUILD_COOKIE_PATH"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


class BahamutError(RuntimeError):
    pass


@dataclass
class CheckResult:
    name: str
    ok: bool
    message: str
    details: list[str] = field(default_factory=list)


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    try:
        return float(value)
    except ValueError:
        return default


def require_cookie() -> str:
    cookie = read_cookie_env("BAHA_COOKIE", "BAHA_COOKIE_JSON")
    if not cookie:
        raise BahamutError(
            "Missing BAHA_COOKIE. Add your Bahamut session cookie to GitHub Secrets."
        )
    return cookie


def cookie_json_to_header(cookie_json: str) -> str:
    try:
        data = json.loads(cookie_json)
    except json.JSONDecodeError as exc:
        raise BahamutError("Cookie JSON secret is not valid JSON.") from exc

    if isinstance(data, dict) and isinstance(data.get("cookies"), list):
        data = data["cookies"]

    cookies: dict[str, str] = {}
    if isinstance(data, list):
        for item in data:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            value = item.get("value")
            if name and value is not None:
                cookies[name] = str(value)
    elif isinstance(data, dict):
        for name, value in data.items():
            if isinstance(value, (str, int, float, bool)):
                cookies[str(name)] = str(value)
    else:
        raise BahamutError("Cookie JSON secret must be a cookie list or object.")

    return "; ".join(f"{name}={value}" for name, value in cookies.items())


def normalize_cookie_secret(cookie: str) -> str:
    cookie = cookie.strip()
    if not cookie:
        return ""
    if cookie[0] in "[{":
        return cookie_json_to_header(cookie)
    return normalize_cookie_header(cookie)


def read_cookie_env(header_name: str, json_name: str) -> str:
    json_cookie = os.getenv(json_name, "")
    if json_cookie.strip():
        return normalize_cookie_secret(json_cookie)
    return normalize_cookie_secret(os.getenv(header_name, ""))


def normalize_cookie_header(cookie: str) -> str:
    normalized = re.sub(r"\s*[\r\n]+\s*", " ", cookie).strip()
    return re.sub(r"^cookie\s*:\s*", "", normalized, flags=re.IGNORECASE)


def merge_cookie_headers(base_cookie: str, override_cookie: str) -> str:
    cookies: dict[str, str] = {}
    for cookie_header in (base_cookie, override_cookie):
        for fragment in normalize_cookie_header(cookie_header).split(";"):
            name, separator, value = fragment.strip().partition("=")
            if name and separator:
                cookies[name] = value
    return "; ".join(f"{name}={value}" for name, value in cookies.items())


def cookies_to_header(cookies: Any) -> str:
    parts: list[str] = []
    for cookie in cookies:
        name = getattr(cookie, "name", "")
        value = getattr(cookie, "value", None)
        if name and value is not None:
            parts.append(f"{name}={value}")
    return "; ".join(parts)


def merge_response_cookies(cookie_header: str, cookies: Any) -> str:
    return merge_cookie_headers(cookie_header, cookies_to_header(cookies))


def apply_response_cookies(session: requests.Session, response: requests.Response) -> bool:
    merged_cookie = merge_response_cookies(session.headers.get("Cookie", ""), response.cookies)
    if not merged_cookie or merged_cookie == session.headers.get("Cookie", ""):
        return False
    session.headers["Cookie"] = merged_cookie
    return True


def make_session(cookie: str, track_refreshed_cookie: bool = False) -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
            "Cookie": cookie,
            "Origin": BASE_WEB_URL,
            "Referer": f"{BASE_WEB_URL}/",
            "X-Requested-With": "XMLHttpRequest",
        }
    )
    if track_refreshed_cookie:
        def remember_response_cookies(
            response: requests.Response, *args: Any, **kwargs: Any
        ) -> requests.Response:
            merged_cookie = merge_response_cookies(
                session.headers.get("Cookie", ""), response.cookies
            )
            if merged_cookie:
                session.headers["Cookie"] = merged_cookie
            return response

        session.hooks["response"].append(remember_response_cookies)
    return session


def csrf_from_cookie(cookie: str) -> str | None:
    for fragment in cookie.split(";"):
        name, _, value = fragment.strip().partition("=")
        if name == "ckBahamutCsrfToken" and value:
            return value
    return None


def cookie_value(cookie: str, target_name: str) -> str | None:
    for fragment in normalize_cookie_header(cookie).split(";"):
        name, _, value = fragment.strip().partition("=")
        if name == target_name and value:
            return value
    return None


def parse_json_response(response: requests.Response) -> dict[str, Any]:
    try:
        data = response.json()
    except json.JSONDecodeError as exc:
        body = response.text[:160].replace("\n", " ")
        raise BahamutError(
            f"Expected JSON but received HTTP {response.status_code}: {body}"
        ) from exc

    if not isinstance(data, dict):
        raise BahamutError(f"Expected JSON object but received {type(data).__name__}.")
    return data


def redact_debug_value(key: str, value: Any, depth: int = 0) -> Any:
    sensitive_markers = ("cookie", "token", "csrf", "session", "password", "secret")
    if any(marker in key.lower() for marker in sensitive_markers):
        return "***"
    if isinstance(value, dict):
        if depth >= 2:
            return f"<object keys={','.join(str(k) for k in list(value)[:8])}>"
        return {
            str(item_key): redact_debug_value(str(item_key), item_value, depth + 1)
            for item_key, item_value in list(value.items())[:12]
        }
    if isinstance(value, list):
        if depth >= 2:
            return f"<list len={len(value)}>"
        return [redact_debug_value(key, item, depth + 1) for item in value[:5]]
    if isinstance(value, str):
        return clean_bahamut_message(value)[:500]
    return value


def response_debug_details(
    label: str,
    response: requests.Response,
    data: dict[str, Any] | None = None,
) -> list[str]:
    details = [f"{label} HTTP {response.status_code}."]
    content_type = response.headers.get("Content-Type", "")
    if content_type:
        details.append(f"{label} content-type: {content_type.split(';', 1)[0]}.")

    if data is None:
        body = clean_bahamut_message(response.text[:500].replace("\n", " "))
        if body:
            details.append(f"{label} body preview: {body}")
        return details

    keys = ", ".join(str(key) for key in data.keys()) or "<none>"
    details.append(f"{label} JSON keys: {keys}.")
    for key in ("error", "code", "status", "success", "ok", "message", "msg", "errorMessage", "data"):
        if key in data:
            value = redact_debug_value(key, data[key])
            details.append(f"{label} {key}: {json.dumps(value, ensure_ascii=False)}")
    return details


def get_csrf_token(session: requests.Session) -> str:
    response = session.get(f"{BASE_WEB_URL}/ajax/get_csrf_token.php", timeout=20)
    if response.status_code in {401, 403}:
        raise BahamutError("Cookie is invalid or expired while fetching CSRF token.")
    response.raise_for_status()
    token = response.text.strip()
    if not token or "<html" in token.lower():
        raise BahamutError("Could not fetch CSRF token. Cookie may be invalid.")
    return token


def prepare_csrf(session: requests.Session, cookie: str) -> str:
    token = csrf_from_cookie(cookie) or get_csrf_token(session)
    session.headers.update({"x-bahamut-csrf-token": token})
    return token


def api_says_success(data: dict[str, Any]) -> bool:
    if data.get("error") is False:
        return True
    if data.get("success") is True:
        return True
    if data.get("ok") is True:
        return True
    code_value = data.get("code", data.get("status", ""))
    code = str(code_value).lower()
    return code in {"0", "success", "ok"}


def api_message(data: dict[str, Any]) -> str:
    error = data.get("error")
    if isinstance(error, dict):
        message = error.get("message")
        if isinstance(message, str) and message.strip():
            return message.strip()

    for key in ("message", "msg", "errorMessage", "data"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return json.dumps(data, ensure_ascii=False)


def clean_bahamut_message(message: str) -> str:
    text = re.sub(
        r'<i\b[^>]*class=["\'][^"\']*material-icons[^"\']*["\'][^>]*>[^<]*</i>',
        "",
        message,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(
        r"^(?:check|check_box)\s*(?=(?:每日)?(?:簽到|签到))",
        "",
        text,
        flags=re.IGNORECASE,
    )
    return re.sub(r"\s+", " ", text).strip()


def looks_already_done(message: str) -> bool:
    return any(
        marker in message
        for marker in (
            "已簽到",
            "已签到",
            "已經簽到",
            "已经签到",
            "今日已",
            "already",
            "重複",
            "重复",
        )
    )


def looks_login_required(message: str) -> bool:
    return any(
        marker in message.lower()
        for marker in (
            "請先登入",
            "请先登录",
            "重新登入",
            "重新登录",
            "login",
            "not logged in",
        )
    )


def looks_operation_failed(message: str) -> bool:
    return any(
        marker in message.lower()
        for marker in (
            "失敗",
            "失败",
            "錯誤",
            "错误",
            "error",
            "failed",
        )
    )


def looks_signin_success(message: str) -> bool:
    normalized = clean_bahamut_message(message)
    return any(
        marker in normalized
        for marker in (
            "每日簽到已達成",
            "每日签到已达成",
        )
    )


def iter_text_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        texts: list[str] = []
        for item in value.values():
            texts.extend(iter_text_values(item))
        return texts
    if isinstance(value, list):
        texts = []
        for item in value:
            texts.extend(iter_text_values(item))
        return texts
    return []


def daily_signin_succeeded(data: dict[str, Any], message: str) -> bool:
    text_values = iter_text_values(data)
    text = "\n".join(text_values or [message])
    if looks_login_required(text):
        return False
    if api_says_success(data) or looks_already_done(text) or looks_signin_success(text):
        return True

    status = data.get("data")
    if not isinstance(status, dict):
        return False

    button_text = str(status.get("btnMessage", ""))
    has_signin_status = any(key in status for key in ("days", "totalWeeks", "dialogInfo"))
    if "check_box" in button_text and has_signin_status:
        return True
    if "check_box" in button_text and ("簽到" in button_text or "签到" in button_text):
        return True
    if "已達成" in button_text or "已达成" in button_text:
        return True
    return False


def looks_guild_sign_success(message: str) -> bool:
    return any(
        marker in message
        for marker in (
            "簽到成功",
            "签到成功",
            "簽到完成",
            "签到完成",
            "公會簽到",
            "公会签到",
            "已簽到",
            "已签到",
            "獲得",
            "获得",
            "經驗",
            "经验",
            "巴幣",
            "巴币",
            "GP",
        )
    )


def guild_sign_succeeded(data: dict[str, Any], message: str) -> bool:
    if looks_login_required(message) or looks_operation_failed(message):
        return False
    return api_says_success(data) or looks_already_done(message) or looks_guild_sign_success(message)


def daily_signin_status(session: requests.Session, token: str) -> CheckResult:
    response = session.post(
        f"{BASE_API_URL}/user/v1/signin.php",
        data={"action": "2"},
        headers={"x-bahamut-csrf-token": token},
        timeout=20,
    )
    if response.status_code in {401, 403}:
        return CheckResult(
            "每日签到状态",
            False,
            "Cookie is invalid or expired.",
            response_debug_details("Daily status action=2", response),
        )

    response.raise_for_status()
    data = parse_json_response(response)
    details = response_debug_details("Daily status action=2", response, data)
    message = clean_bahamut_message(api_message(data))
    ok = daily_signin_succeeded(data, message)
    if not ok:
        message = f"Could not verify that daily check-in was completed: {message}"
    return CheckResult("每日签到状态", ok, message, details)


def daily_signin_needs_cookie_retry(result: CheckResult) -> bool:
    if result.ok:
        return False
    text = "\n".join([result.message, *result.details])
    return looks_login_required(text) or "NO_LOGIN" in text or "401" in text


def daily_signin(session: requests.Session, token: str) -> CheckResult:
    base_cookie = read_cookie_env("BAHA_COOKIE", "BAHA_COOKIE_JSON")
    daily_cookie = read_cookie_env("BAHA_DAILY_COOKIE", "BAHA_DAILY_COOKIE_JSON")
    guild_cookie = read_cookie_env("BAHA_GUILD_COOKIE", "BAHA_GUILD_COOKIE_JSON")

    def run_attempt(
        attempt_session: requests.Session,
        attempt_token: str,
        original_cookie: str,
        allow_refresh_write: bool,
        label: str,
    ) -> CheckResult:
        response = attempt_session.post(
            f"{BASE_API_URL}/user/v1/signin.php",
            data={"action": "1"},
            headers={"x-bahamut-csrf-token": attempt_token},
            timeout=20,
        )

        if response.status_code in {401, 403}:
            return CheckResult(
                "每日签到",
                False,
                "Cookie is invalid or expired.",
                response_debug_details(label, response),
            )

        response.raise_for_status()
        data = parse_json_response(response)
        details = response_debug_details(label, response, data)
        message = clean_bahamut_message(api_message(data))
        ok = daily_signin_succeeded(data, message)
        if ok:
            status = daily_signin_status(attempt_session, attempt_token)
            details.extend(status.details)
            if not status.ok:
                return CheckResult("每日签到", False, status.message, [message, *details])
        elif "簽到 +" in message or "签到 +" in message:
            message = f"Daily check-in was not completed; current prompt: {message}"
        if ok and allow_refresh_write and write_refreshed_cookie_file(
            original_cookie,
            attempt_session.headers.get("Cookie", ""),
            DAILY_COOKIE_REFRESH_FILE_ENV,
        ):
            details.append("Refreshed BAHA_DAILY_COOKIE was captured for the workflow.")
        return CheckResult("每日签到", ok, message, details)

    original_daily_cookie = session.headers.get("Cookie", "")
    if daily_cookie:
        merged_cookie = merge_cookie_headers(base_cookie, daily_cookie) if base_cookie else daily_cookie
        original_daily_cookie = merged_cookie
        session = make_session(merged_cookie)
        token = prepare_csrf(session, merged_cookie)

    result = run_attempt(
        session,
        token,
        original_daily_cookie,
        bool(daily_cookie),
        "Daily sign action=1",
    )
    allow_guild_cookie_retry = env_bool("ALLOW_DAILY_GUILD_COOKIE_FALLBACK", False)
    if not daily_signin_needs_cookie_retry(result) or not guild_cookie or not allow_guild_cookie_retry:
        return result

    retry_cookie = original_daily_cookie
    for cookie in (base_cookie, daily_cookie, guild_cookie):
        retry_cookie = merge_cookie_headers(retry_cookie, cookie)
    if not retry_cookie or retry_cookie == original_daily_cookie:
        return result

    retry_details = [
        *result.details,
        "Daily sign-in looked logged out; retrying once with BAHA_GUILD_COOKIE merged.",
    ]
    retry_session = make_session(retry_cookie)
    retry_token = prepare_csrf(retry_session, retry_cookie)
    retry_result = run_attempt(
        retry_session,
        retry_token,
        retry_cookie,
        True,
        "Daily sign retry with guild cookie action=1",
    )
    retry_result.details = [*retry_details, *retry_result.details]
    if retry_result.ok:
        return retry_result

    guild_only_cookie = normalize_cookie_header(guild_cookie)
    if guild_only_cookie and guild_only_cookie != retry_cookie:
        guild_only_details = [
            *retry_result.details,
            "Merged retry also failed; retrying once with BAHA_GUILD_COOKIE only.",
        ]
        guild_only_session = make_session(guild_only_cookie)
        guild_only_token = prepare_csrf(guild_only_session, guild_only_cookie)
        guild_only_result = run_attempt(
            guild_only_session,
            guild_only_token,
            guild_only_cookie,
            True,
            "Daily sign retry with guild-only cookie action=1",
        )
        guild_only_result.details = [*guild_only_details, *guild_only_result.details]
        if guild_only_result.ok:
            return guild_only_result
        retry_result = CheckResult(
            "每日签到",
            False,
            f"{retry_result.message}; guild-only retry also failed: {guild_only_result.message}",
            guild_only_result.details,
        )

    return CheckResult(
        "每日签到",
        False,
        f"{result.message}; retry also failed: {retry_result.message}",
        retry_result.details,
    )


def detect_ad_bonus(session: requests.Session) -> CheckResult:
    """Only detect possible ad bonus entrypoints. Never claim or complete ads."""
    candidates = [
        f"{BASE_WEB_URL}/",
        f"{BASE_WEB_URL}/dailySign.php",
        f"{BASE_WEB_URL}/signin.php",
    ]
    markers = ("廣告", "广告", "加倍", "兩倍", "两倍", "2倍")

    for url in candidates:
        try:
            response = session.get(url, timeout=20)
        except requests.RequestException as exc:
            return CheckResult("广告加倍提醒", True, f"Could not inspect ad bonus: {exc}")

        if response.status_code in {404, 405}:
            continue
        if response.status_code in {401, 403}:
            return CheckResult("广告加倍提醒", True, "Login expired; cannot inspect ad bonus.")
        if any(marker in response.text for marker in markers):
            return CheckResult(
                "广告加倍提醒",
                True,
                "Possible ad bonus entry found. Please claim it manually in Bahamut.",
            )

    return CheckResult(
        "广告加倍提醒",
        True,
        "No obvious ad bonus entry found. Manual check may still be needed.",
    )


def guild_checkin(session: requests.Session, token: str) -> CheckResult:
    base_cookie = read_cookie_env("BAHA_COOKIE", "BAHA_COOKIE_JSON")
    guild_cookie = read_cookie_env("BAHA_GUILD_COOKIE", "BAHA_GUILD_COOKIE_JSON")
    original_guild_cookie = session.headers.get("Cookie", "")
    if base_cookie:
        merged_cookie = merge_cookie_headers(base_cookie, guild_cookie) if guild_cookie else base_cookie
        original_guild_cookie = merged_cookie
        session = make_session(merged_cookie)
        token = prepare_csrf(session, merged_cookie)

    response = session.get(f"{BASE_API_URL}/guild/v2/guild_my.php", timeout=20)
    if response.status_code in {401, 403}:
        return CheckResult("公会签到", False, "Cookie is invalid or expired.")
    response.raise_for_status()
    data = parse_json_response(response)

    guilds = data.get("data") or data.get("guilds") or data.get("list") or []
    if isinstance(guilds, dict):
        guilds = list(guilds.values())
    if not isinstance(guilds, list):
        return CheckResult("公会签到", False, f"Unexpected guild list: {api_message(data)}")
    details: list[str] = []
    api_guilds = normalize_guilds(guilds)
    if api_guilds:
        details.append(
            "Guild API found guilds: "
            + ", ".join(f"{guild.get('name')} ({guild.get('sn')})" for guild in api_guilds)
        )
    else:
        details.append("Guild API returned 0 guilds.")

    profile_result = fetch_profile_guilds(session)
    profile_guilds = normalize_guilds(profile_result.guilds)
    details.extend(profile_result.details)

    guilds = merge_guild_lists(api_guilds, profile_guilds)
    if not guilds:
        return CheckResult(
            "公会签到",
            True,
            "No joined guilds found from guild API or profile page.",
            details,
        )

    details.append(f"Found {len(guilds)} unique guild(s) from guild API and profile page.")
    any_failure = False
    delay_seconds = max(0.0, env_float("GUILD_CHECKIN_DELAY_SECONDS", 1.0))
    for index, guild in enumerate(guilds):
        if not isinstance(guild, dict):
            continue
        guild_id = guild.get("guild_id") or guild.get("sn") or guild.get("id")
        guild_name = guild.get("guild_name") or guild.get("name") or str(guild_id)
        if not guild_id:
            details.append(f"{guild_name}: skipped because guild id was not found")
            any_failure = True
            continue

        try:
            guild_headers = {
                "Origin": BASE_GUILD_URL,
                "Referer": f"{BASE_GUILD_URL}/guild.php?sn={guild_id}",
                "x-bahamut-csrf-token": token,
            }
            try:
                guild_page_response = session.get(
                    f"{BASE_GUILD_URL}/guild.php",
                    params={"sn": guild_id},
                    headers=guild_headers,
                    timeout=20,
                )
                apply_response_cookies(session, guild_page_response)
            except requests.RequestException:
                pass

            sign_response = session.post(
                f"{BASE_GUILD_URL}/ajax/guildSign.php",
                data={"sn": guild_id},
                headers=guild_headers,
                timeout=20,
            )
            sign_response.raise_for_status()
            apply_response_cookies(session, sign_response)
            sign_data = parse_json_response(sign_response)
            message = clean_bahamut_message(api_message(sign_data))
            ok = guild_sign_succeeded(sign_data, message)
            any_failure = any_failure or not ok
            status = "OK" if ok else "FAIL"
            details.append(f"{status} {guild_name} ({guild_id}): {message}")
        except requests.RequestException as exc:
            any_failure = True
            details.append(f"FAIL {guild_name} ({guild_id}): request failed: {exc}")
        except BahamutError as exc:
            any_failure = True
            details.append(f"FAIL {guild_name} ({guild_id}): {exc}")
        if delay_seconds and index < len(guilds) - 1:
            time.sleep(delay_seconds)

    if not any_failure and write_refreshed_cookie_file(
        original_guild_cookie,
        session.headers.get("Cookie", ""),
        GUILD_COOKIE_REFRESH_FILE_ENV,
    ):
        details.append("Refreshed BAHA_GUILD_COOKIE was captured for the workflow.")

    return CheckResult(
        "公会签到",
        not any_failure,
        "Guild check-in completed." if not any_failure else "Some guilds failed.",
        details,
    )


def normalize_guilds(guilds: list[Any]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for guild in guilds:
        if not isinstance(guild, dict):
            continue
        guild_id = guild.get("guild_id") or guild.get("sn") or guild.get("id")
        guild_name = guild.get("guild_name") or guild.get("name") or str(guild_id)
        if guild_id:
            normalized.append({"sn": str(guild_id), "name": str(guild_name)})
    return normalized


def merge_guild_lists(*guild_lists: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for guilds in guild_lists:
        for guild in guilds:
            guild_id = str(guild.get("sn") or guild.get("guild_id") or guild.get("id") or "")
            if guild_id and guild_id not in merged:
                merged[guild_id] = {"sn": guild_id, "name": guild.get("name") or guild_id}
    return list(merged.values())


@dataclass
class GuildFetchResult:
    guilds: list[dict[str, Any]]
    details: list[str] = field(default_factory=list)


def fetch_profile_guilds(session: requests.Session) -> GuildFetchResult:
    cookie_header = session.headers.get("Cookie", "")
    owner = cookie_value(cookie_header, "BAHAID") or cookie_value(cookie_header, "MB_BAHAID")
    if not owner:
        return GuildFetchResult([], ["Profile fallback skipped: BAHAID was not found in cookie."])

    response = session.get(
        "https://home.gamer.com.tw/profile/my_guild.php",
        params={"owner": owner},
        timeout=20,
    )
    if response.status_code in {401, 403, 404}:
        return GuildFetchResult(
            [],
            [f"Profile fallback HTTP {response.status_code} for owner={owner}."],
        )
    response.raise_for_status()
    guilds = parse_profile_guilds(response.text)
    details = [f"Profile fallback fetched owner={owner}, HTTP {response.status_code}."]
    if guilds:
        details.append(
            "Profile fallback found guilds: "
            + ", ".join(f"{guild.get('name')} ({guild.get('sn')})" for guild in guilds)
        )
    else:
        details.append("Profile fallback parsed 0 guild links. The page layout may have changed or the profile page may be hiding guilds from this session.")
    return GuildFetchResult(guilds, details)


def parse_profile_guilds(html: str) -> list[dict[str, Any]]:
    seen: set[str] = set()
    guilds: list[dict[str, Any]] = []
    link_pattern = re.compile(
        r'<a\b[^>]*href=["\']([^"\']*(?:guild\.gamer\.com\.tw|guild\.php|/guild/)[^"\']*)["\'][^>]*>(.*?)</a>',
        re.IGNORECASE | re.DOTALL,
    )
    id_patterns = (
        re.compile(r"[?&]sn=(\d+)", re.IGNORECASE),
        re.compile(r"/guild/(\d+)", re.IGNORECASE),
        re.compile(r"guild_sn=(\d+)", re.IGNORECASE),
        re.compile(r"gsn=(\d+)", re.IGNORECASE),
    )
    for match in link_pattern.finditer(html):
        href = match.group(1)
        guild_id = None
        for id_pattern in id_patterns:
            id_match = id_pattern.search(href)
            if id_match:
                guild_id = id_match.group(1)
                break
        if not guild_id:
            continue
        if guild_id in seen:
            continue
        name = re.sub(r"<[^>]+>", "", match.group(2))
        name = re.sub(r"\s+", " ", name).strip() or guild_id
        seen.add(guild_id)
        guilds.append({"sn": guild_id, "name": name})
    return guilds


def extract_answer_from_source(html: str, question: str) -> str | None:
    normalized_question = re.sub(r"\s+", "", question)
    if not normalized_question:
        return None

    candidates = re.findall(
        r"(?:答案|Ans(?:wer)?|[aAＡ])\s*[.．:：]?\s*([1-4１-４ABCD])",
        html,
        flags=re.IGNORECASE,
    )
    for candidate in candidates:
        answer = normalize_answer(candidate.strip())
        if answer:
            return answer

    compact_html = re.sub(r"\s+", "", html)
    question_index = compact_html.find(normalized_question[:20])
    if question_index == -1:
        return None
    window = compact_html[question_index : question_index + 500]
    match = re.search(
        r"(?:答案|Answer|Ans|[aAＡ])\s*[.．:：]?\s*([1-4１-４ABCD])",
        window,
        re.IGNORECASE,
    )
    return normalize_answer(match.group(1).strip()) if match else None


def normalize_answer(value: str) -> str | None:
    table = str.maketrans("１２３４ＡＢＣＤabcd", "1234ABCDABCD")
    normalized = value.translate(table).strip().upper()
    if normalized in {"A", "B", "C", "D"}:
        return str("ABCD".index(normalized) + 1)
    if normalized in {"1", "2", "3", "4"}:
        return normalized
    return None


def fetch_blackxblue_answer(session: requests.Session, question: str) -> str | None:
    response = session.get(
        f"{BASE_API_URL}/home/v2/creation_list.php",
        params={"owner": "blackXblue"},
        timeout=20,
    )
    response.raise_for_status()
    data = parse_json_response(response)
    creations = ((data.get("data") or {}).get("list") if isinstance(data.get("data"), dict) else None) or []
    if not isinstance(creations, list):
        return None

    for creation in creations[:5]:
        if not isinstance(creation, dict):
            continue
        sn = creation.get("csn") or creation.get("sn")
        if not sn:
            continue
        article = session.get(f"https://home.gamer.com.tw/artwork.php", params={"sn": sn}, timeout=20)
        article.raise_for_status()
        answer = extract_answer_from_source(article.text, question)
        if answer:
            return answer
    return None


def fetch_collection_answer(session: requests.Session, question: str) -> str | None:
    response = session.get(
        "https://script.google.com/macros/s/AKfycbxYKwsjq6jB2Oo0xwz4bmkd3-5hdguopA6VJ5KD/exec",
        params={"question": question, "type": "quiz"},
        timeout=20,
    )
    response.raise_for_status()
    data = parse_json_response(response)
    payload = data.get("data") if isinstance(data.get("data"), dict) else data
    return normalize_answer(str(payload.get("answer", ""))) if isinstance(payload, dict) else None


def fetch_anime_answer(session: requests.Session, question: str) -> str | None:
    for fetcher in (fetch_blackxblue_answer, fetch_collection_answer):
        try:
            answer = fetcher(session, question)
        except (requests.RequestException, BahamutError):
            continue
        if answer:
            return answer
    return None


def anime_quiz(session: requests.Session, token: str) -> CheckResult:
    anime_cookie = read_cookie_env("BAHA_ANIME_COOKIE", "BAHA_ANIME_COOKIE_JSON")
    used_anime_cookie = bool(anime_cookie)
    if anime_cookie:
        base_cookie = read_cookie_env("BAHA_COOKIE", "BAHA_COOKIE_JSON")
        merged_cookie = merge_cookie_headers(base_cookie, anime_cookie)
        session = make_session(merged_cookie)
        token = prepare_csrf(session, merged_cookie)

    anime_headers = {
        "Origin": BASE_ANI_URL,
        "Referer": f"{BASE_ANI_URL}/",
        "x-bahamut-csrf-token": token,
    }

    try:
        session.get(f"{BASE_ANI_URL}/", headers=anime_headers, timeout=20)
    except requests.RequestException:
        pass

    response = session.get(
        f"{BASE_ANI_URL}/ajax/animeGetQuestion.php",
        params={"t": "1"},
        headers=anime_headers,
        timeout=20,
    )
    if response.status_code in {401, 403}:
        cookie_name = "BAHA_ANIME_COOKIE" if used_anime_cookie else "BAHA_COOKIE"
        return CheckResult(
            "動畫瘋答题",
            False,
            f"Ani-Gamer rejected {cookie_name}. Open ani.gamer.com.tw in the browser, confirm it is logged in, then refresh {cookie_name} from an ani.gamer.com.tw request. The cookie must be saved as one single line.",
        )
    response.raise_for_status()
    data = parse_json_response(response)
    if not api_says_success(data) and looks_already_done(api_message(data)):
        return CheckResult("動畫瘋答题", True, api_message(data))

    payload = data.get("data") if isinstance(data.get("data"), dict) else data
    question = str(payload.get("question") or payload.get("title") or "").strip()
    question_id = payload.get("question_id") or payload.get("sn") or payload.get("id")
    if not question:
        return CheckResult("動畫瘋答题", True, f"No quiz question found: {api_message(data)}")

    answer = fetch_anime_answer(session, question)
    if not answer:
        return CheckResult(
            "動畫瘋答题",
            True,
            f"Skipped because no answer was found for question: {question}",
        )

    post_data: dict[str, Any] = {"token": token, "ans": answer}
    if question_id:
        post_data["sn"] = question_id
    answer_response = session.post(
        f"{BASE_ANI_URL}/ajax/animeAnsQuestion.php",
        data={**post_data, "t": "1"},
        headers=anime_headers,
        timeout=20,
    )
    answer_response.raise_for_status()
    answer_data = parse_json_response(answer_response)
    message = api_message(answer_data)
    ok = api_says_success(answer_data) or looks_already_done(message)
    return CheckResult("動畫瘋答题", ok, message)


def send_discord(message: str) -> None:
    webhook = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
    if not webhook:
        return
    requests.post(webhook, json={"content": message[:1900]}, timeout=20).raise_for_status()


def send_telegram(message: str) -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(
        url,
        json={"chat_id": chat_id, "text": message[:3900]},
        timeout=20,
    ).raise_for_status()


def result_to_markdown(results: list[CheckResult]) -> str:
    lines = ["# Bahamut check-in summary", ""]
    for result in results:
        icon = "OK" if result.ok else "FAIL"
        lines.append(f"- **{result.name}**: {icon} - {result.message}")
        for detail in result.details:
            lines.append(f"  - {detail}")
    return "\n".join(lines) + "\n"


def write_github_summary(markdown: str) -> None:
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    with open(summary_path, "a", encoding="utf-8") as summary:
        summary.write(markdown)


def write_refreshed_cookie_file(
    original_cookie: str,
    refreshed_cookie: str,
    env_name: str = COOKIE_REFRESH_FILE_ENV,
) -> bool:
    path = os.getenv(env_name, "").strip()
    refreshed_cookie = normalize_cookie_header(refreshed_cookie)
    if not path or not refreshed_cookie or refreshed_cookie == original_cookie:
        return False

    print(f"::add-mask::{refreshed_cookie}")
    try:
        with open(path, "w", encoding="utf-8", newline="\n") as cookie_file:
            cookie_file.write(refreshed_cookie + "\n")
    except OSError as exc:
        print(f"Could not write refreshed cookie file: {exc}", file=sys.stderr)
        return False
    return True


def main() -> int:
    results: list[CheckResult] = []
    cookie = ""
    session: requests.Session | None = None

    try:
        cookie = require_cookie()
        session = make_session(cookie)
        token = prepare_csrf(session, cookie)

        if env_bool("ENABLE_GUILD_CHECKIN", True):
            guild_result = guild_checkin(session, token)
        else:
            guild_result = CheckResult("公会签到", True, "Skipped by configuration.")

        daily_result = daily_signin(session, token)
        ad_result = detect_ad_bonus(session)
        results.extend([daily_result, ad_result, guild_result])

        if env_bool("ENABLE_ANIME_QUIZ", False):
            results.append(anime_quiz(session, token))
        else:
            results.append(CheckResult("動畫瘋答题", True, "Skipped by configuration."))

        if (
            results
            and results[0].ok
            and session is not None
            and write_refreshed_cookie_file(cookie, session.headers.get("Cookie", ""))
        ):
            results.append(
                CheckResult(
                    "Cookie refresh",
                    True,
                    "Refreshed BAHA_COOKIE was captured for the workflow.",
                )
            )

    except requests.RequestException as exc:
        results.append(CheckResult("运行状态", False, f"Network request failed: {exc}"))
    except BahamutError as exc:
        results.append(CheckResult("运行状态", False, str(exc)))

    summary = result_to_markdown(results)
    print(summary)
    write_github_summary(summary)

    for sender in (send_discord, send_telegram):
        try:
            sender(summary)
        except requests.RequestException as exc:
            print(f"Notification failed: {exc}", file=sys.stderr)

    return 0 if results and all(result.ok for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
