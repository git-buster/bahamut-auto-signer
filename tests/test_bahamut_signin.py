import os

import pytest
from requests import Response
from requests.cookies import RequestsCookieJar

import scripts.bahamut_signin as signer
from scripts.bahamut_signin import (
    BahamutError,
    api_message,
    api_says_success,
    apply_response_cookies,
    clean_bahamut_message,
    cookie_value,
    daily_signin,
    daily_signin_succeeded,
    env_bool,
    env_float,
    extract_answer_from_source,
    guild_sign_succeeded,
    guild_checkin,
    looks_already_done,
    looks_login_required,
    looks_signin_success,
    merge_guild_lists,
    merge_cookie_headers,
    merge_response_cookies,
    normalize_answer,
    normalize_cookie_header,
    normalize_cookie_secret,
    parse_profile_guilds,
    read_cookie_env,
    require_cookie,
    response_debug_details,
    write_refreshed_cookie_file,
)


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self._headers = {"Cookie": "BAHAID=user"}

    def get(self, *args, **kwargs):
        return self.responses.pop(0)

    def post(self, *args, **kwargs):
        return self.responses.pop(0)

    @property
    def headers(self):
        return self._headers


def json_response(data, status_code=200):
    response = Response()
    response.status_code = status_code
    response._content = data.encode("utf-8")
    response.headers["Content-Type"] = "application/json"
    return response


def test_require_cookie_fails_without_secret(monkeypatch):
    monkeypatch.delenv("BAHA_COOKIE", raising=False)

    with pytest.raises(BahamutError) as exc:
        require_cookie()

    assert "BAHA_COOKIE" in str(exc.value)


def test_env_bool_parses_common_values(monkeypatch):
    monkeypatch.setenv("FEATURE_FLAG", "true")
    assert env_bool("FEATURE_FLAG") is True

    monkeypatch.setenv("FEATURE_FLAG", "0")
    assert env_bool("FEATURE_FLAG", True) is False

    monkeypatch.delenv("FEATURE_FLAG", raising=False)
    assert env_bool("FEATURE_FLAG", True) is True


def test_env_float_parses_values(monkeypatch):
    monkeypatch.setenv("DELAY", "1.5")
    assert env_float("DELAY", 0.0) == 1.5

    monkeypatch.setenv("DELAY", "bad")
    assert env_float("DELAY", 2.0) == 2.0

    monkeypatch.delenv("DELAY", raising=False)
    assert env_float("DELAY", 3.0) == 3.0


def test_success_and_already_done_detection():
    assert api_says_success({"error": False}) is True
    assert api_says_success({"success": True}) is True
    assert api_says_success({"ok": True}) is True
    assert api_says_success({"code": 0}) is True
    assert looks_already_done("今日已簽到") is True
    assert looks_already_done("今天您已經簽到過了喔") is True
    assert not looks_signin_success('<i class="material-icons">check</i>簽到 + 100 巴幣')
    assert not daily_signin_succeeded({"data": "check簽到 + 100 巴幣"}, "check簽到 + 100 巴幣")
    assert looks_signin_success('<i class="material-icons">check_box</i>每日簽到已達成')
    assert clean_bahamut_message('<i class="material-icons">check</i>簽到 + 100 巴幣') == "簽到 + 100 巴幣"
    assert clean_bahamut_message("check簽到 + 100 巴幣") == "簽到 + 100 巴幣"
    assert looks_login_required("請先登入") is True
    assert guild_sign_succeeded({"ok": True}, "OK") is True
    assert guild_sign_succeeded({"error": False}, "請先登入") is False
    assert guild_sign_succeeded({}, "公會簽到成功，獲得 1 GP") is True


def test_api_message_reads_nested_error_message():
    assert (
        api_message({"error": {"code": 8892, "message": "今天您已經簽到過了喔"}})
        == "今天您已經簽到過了喔"
    )


def test_extract_answer_from_source_near_question():
    html = "<p>今天的題目是什麼?</p><p>A:2</p>"

    assert extract_answer_from_source(html, "今天的題目是什麼?") == "2"


def test_normalize_answer_accepts_letters_and_full_width_digits():
    assert normalize_answer("B") == "2"
    assert normalize_answer("３") == "3"


def test_normalize_cookie_header_removes_line_breaks():
    assert normalize_cookie_header("a=1;\n b=2;\r\nc=3") == "a=1; b=2; c=3"
    assert normalize_cookie_header("Cookie: a=1; b=2") == "a=1; b=2"
    assert cookie_value("BAHAID=demo_user; x=1", "BAHAID") == "demo_user"


def test_cookie_json_secret_converts_to_cookie_header(monkeypatch):
    cookie_json = '[{"name": "BAHAID", "value": "user"}, {"name": "shared", "value": "new"}]'
    assert normalize_cookie_secret(cookie_json) == "BAHAID=user; shared=new"

    monkeypatch.setenv("BAHA_COOKIE", "BAHAID=old")
    monkeypatch.setenv("BAHA_COOKIE_JSON", cookie_json)
    assert read_cookie_env("BAHA_COOKIE", "BAHA_COOKIE_JSON") == "BAHAID=user; shared=new"


def test_merge_cookie_headers_overrides_duplicate_names():
    assert (
        merge_cookie_headers("BAHAID=user; shared=old", "ani=1; shared=new")
        == "BAHAID=user; shared=new; ani=1"
    )


def test_merge_response_cookies_updates_cookie_header():
    cookies = RequestsCookieJar()
    cookies.set("shared", "new")
    cookies.set("fresh", "1")

    assert (
        merge_response_cookies("BAHAID=user; shared=old", cookies)
        == "BAHAID=user; shared=new; fresh=1"
    )


def test_apply_response_cookies_updates_session_header():
    class Session:
        headers = {"Cookie": "BAHAID=user; shared=old"}

    response = Response()
    response.cookies.set("shared", "new")
    response.cookies.set("guild_session", "1")

    assert apply_response_cookies(Session(), response) is True
    assert Session.headers["Cookie"] == "BAHAID=user; shared=new; guild_session=1"


def test_write_refreshed_cookie_file_only_when_changed(monkeypatch, tmp_path):
    cookie_path = tmp_path / "cookie.txt"
    monkeypatch.setenv("BAHA_REFRESHED_COOKIE_PATH", str(cookie_path))

    assert write_refreshed_cookie_file("a=1", "a=1") is False
    assert not cookie_path.exists()

    assert write_refreshed_cookie_file("a=1", "a=2; b=3") is True
    assert cookie_path.read_text(encoding="utf-8").strip() == "a=2; b=3"


def test_write_refreshed_cookie_file_uses_custom_env(monkeypatch, tmp_path):
    cookie_path = tmp_path / "guild_cookie.txt"
    monkeypatch.setenv("BAHA_REFRESHED_GUILD_COOKIE_PATH", str(cookie_path))

    assert write_refreshed_cookie_file(
        "a=1",
        "a=1; guild_session=2",
        "BAHA_REFRESHED_GUILD_COOKIE_PATH",
    ) is True
    assert cookie_path.read_text(encoding="utf-8").strip() == "a=1; guild_session=2"


def test_daily_signin_fails_when_status_cannot_verify_completion():
    session = FakeSession(
        [
            json_response('{"error": false, "message": "OK"}'),
            json_response('{"data": {"btnMessage": "每日簽到"}}'),
        ]
    )

    result = daily_signin(session, "token")

    assert result.ok is False
    assert "Could not verify" in result.message


def test_daily_signin_reports_reward_prompt_as_incomplete():
    session = FakeSession(
        [
            json_response('{"data": "<i class=\\"material-icons\\">check</i>簽到 + 100 巴幣"}'),
        ]
    )

    result = daily_signin(session, "token")

    assert result.ok is False
    assert result.message == "Daily check-in was not completed; current prompt: 簽到 + 100 巴幣"
    assert any("Daily sign action=1 HTTP 200." == detail for detail in result.details)
    assert any("Daily sign action=1 data" in detail for detail in result.details)


def test_daily_signin_writes_main_cookie_refresh(monkeypatch, tmp_path):
    refresh_path = tmp_path / "refreshed_cookie.txt"
    session = FakeSession(
        [
            json_response('{"error": false, "message": "OK"}'),
            json_response(
                '{"data": {"btnMessage": "<i class=\\"material-icons\\">check_box</i>每日簽到已達成"}}'
            ),
        ]
    )
    response_cookies = RequestsCookieJar()
    response_cookies.set("main_refresh", "new")
    session.responses[0].cookies = response_cookies

    monkeypatch.setenv("BAHA_COOKIE_JSON", '[{"name": "shared", "value": "base"}]')
    monkeypatch.setenv("BAHA_REFRESHED_COOKIE_PATH", str(refresh_path))

    result = daily_signin(session, "base-token")

    assert result.ok is True
    assert refresh_path.read_text(encoding="utf-8").strip() == "BAHAID=user; main_refresh=new"


def test_daily_signin_retries_with_guild_cookie_on_no_login(monkeypatch):
    captured = []
    daily_session = FakeSession(
        [
            json_response(
                '{"error": {"code": 401, "message": "簽到 + 100 巴幣", "status": "NO_LOGIN"}}'
            ),
        ]
    )
    retry_session = FakeSession(
        [
            json_response('{"error": false, "message": "OK"}'),
            json_response(
                '{"data": {"btnMessage": "<i class=\\"material-icons\\">check_box</i>每日簽到已達成"}}'
            ),
        ]
    )
    sessions = [retry_session]

    def fake_make_session(cookie):
        captured.append(cookie)
        return sessions.pop(0)

    monkeypatch.setenv("BAHA_COOKIE_JSON", '[{"name": "shared", "value": "base"}]')
    monkeypatch.setenv(
        "BAHA_GUILD_COOKIE_JSON",
        '[{"name": "guild", "value": "1"}, {"name": "shared", "value": "guild"}]',
    )
    monkeypatch.setenv("ALLOW_DAILY_GUILD_COOKIE_FALLBACK", "true")
    monkeypatch.setattr(signer, "make_session", fake_make_session)
    monkeypatch.setattr(signer, "prepare_csrf", lambda session, cookie: "token")

    result = daily_signin(daily_session, "base-token")

    assert result.ok is True
    assert captured[-1] == "BAHAID=user; shared=guild; guild=1"
    assert any("retrying once with BAHA_GUILD_COOKIE" in detail for detail in result.details)


def test_daily_signin_retries_with_guild_only_cookie_if_merge_fails(monkeypatch):
    captured = []
    daily_session = FakeSession(
        [
            json_response(
                '{"error": {"code": 401, "message": "簽到 + 100 巴幣", "status": "NO_LOGIN"}}'
            ),
        ]
    )
    merged_retry_session = FakeSession(
        [
            json_response(
                '{"error": {"code": 401, "message": "請先登入", "status": "NO_LOGIN"}}'
            ),
        ]
    )
    guild_only_session = FakeSession(
        [
            json_response('{"error": false, "message": "OK"}'),
            json_response(
                '{"data": {"btnMessage": "<i class=\\"material-icons\\">check_box</i>每日簽到已達成"}}'
            ),
        ]
    )
    sessions = [merged_retry_session, guild_only_session]

    def fake_make_session(cookie):
        captured.append(cookie)
        return sessions.pop(0)

    monkeypatch.setenv("BAHA_COOKIE_JSON", '[{"name": "shared", "value": "base"}]')
    monkeypatch.setenv(
        "BAHA_GUILD_COOKIE_JSON",
        '[{"name": "guild", "value": "1"}, {"name": "shared", "value": "guild"}]',
    )
    monkeypatch.setenv("ALLOW_DAILY_GUILD_COOKIE_FALLBACK", "true")
    monkeypatch.setattr(signer, "make_session", fake_make_session)
    monkeypatch.setattr(signer, "prepare_csrf", lambda session, cookie: "token")

    result = daily_signin(daily_session, "base-token")

    assert result.ok is True
    assert captured[-1] == "guild=1; shared=guild"
    assert any("BAHA_GUILD_COOKIE only" in detail for detail in result.details)


def test_daily_signin_accepts_completed_button_state():
    data = {
        "data": {
            "days": 7,
            "dialog": "7",
            "prjSigninDays": 0,
            "btnMessage": '<i class="material-icons">check_box</i>每日簽到已達成',
            "totalWeeks": 4,
            "dialogInfo": {
                "title": "連續 7 天簽到",
                "content": "獲得加碼獎勵<br> 500 巴幣",
            },
        }
    }

    assert daily_signin_succeeded(data, api_message(data)) is True


def test_response_debug_details_redacts_sensitive_fields():
    response = json_response(
        '{"error": false, "token": "secret-token", "data": {"csrf": "secret", "message": "OK"}}'
    )
    data = response.json()

    details = response_debug_details("Debug", response, data)
    text = "\n".join(details)

    assert "secret-token" not in text
    assert '"csrf": "***"' in text
    assert "Debug token" not in text
    assert "Debug data" in text


def test_guild_checkin_treats_login_required_message_as_failure():
    session = FakeSession(
        [
            json_response('{"data": [{"sn": "1", "name": "Guild"}]}'),
            json_response("<html></html>"),
            json_response("<html></html>"),
            json_response('{"error": false, "message": "請先登入"}'),
        ]
    )

    result = guild_checkin(session, "token")

    assert result.ok is False
    assert any("FAIL Guild (1)" in detail for detail in result.details)


def test_parse_profile_guilds_extracts_unique_guild_links():
    html = """
    <a href="https://guild.gamer.com.tw/guild.php?sn=123">公會 A</a>
    <a href="//guild.gamer.com.tw/guild.php?sn=456&foo=bar"><span>公會 B</span></a>
    <a href="/guild/789">公會 C</a>
    <a href="https://guild.gamer.com.tw/guild.php?sn=123">公會 A duplicate</a>
    """

    assert parse_profile_guilds(html) == [
        {"sn": "123", "name": "公會 A"},
        {"sn": "456", "name": "公會 B"},
        {"sn": "789", "name": "公會 C"},
    ]


def test_merge_guild_lists_combines_api_and_profile_guilds():
    assert merge_guild_lists(
        [{"sn": "1", "name": "API A"}],
        [{"sn": "1", "name": "Profile A"}, {"sn": "2", "name": "Profile B"}],
    ) == [
        {"sn": "1", "name": "API A"},
        {"sn": "2", "name": "Profile B"},
    ]
