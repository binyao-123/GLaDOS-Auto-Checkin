import os
import json
import time
import random
import cloudscraper
from pypushdeer import PushDeer


CHECKIN_URL = "https://glados.space"
STATUS_URL = "https://glados.space"

HEADERS_BASE = {
    "origin": "https://glados.space",
    "referer": "https://glados.space",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "content-type": "application/json;charset=UTF-8",
}

PAYLOAD = {"token": "glados.cloud"}
# 增加超时时间以适应 Cloudflare 验证过程
TIMEOUT = 30


def push(sckey: str, title: str, text: str):
    if sckey:
        PushDeer(pushkey=sckey).send_text(title, desp=text)


def safe_json(resp):
    try:
        return resp.json()
    except Exception:
        return {}


def main():
    sckey = os.getenv("SENDKEY", "")
    cookies_env = os.getenv("COOKIES", "")
    cookies = [c.strip() for c in cookies_env.split("&") if c.strip()]

    if not cookies:
        push(sckey, "GLaDOS 签到", "❌ 未检测到 COOKIES")
        return

    # 使用 cloudscraper 创建会话
    scraper = cloudscraper.create_scraper()
    ok = fail = repeat = 0
    lines = []

    for idx, cookie in enumerate(cookies, 1):
        headers = dict(HEADERS_BASE)
        headers["cookie"] = cookie

        email = "unknown"
        points = "-"
        days = "-"

        try:
            # 使用 scraper 会话发送请求
            r = scraper.post(
                CHECKIN_URL,
                headers=headers,
                data=json.dumps(PAYLOAD),
                timeout=TIMEOUT,
            )

            j = safe_json(r)
            msg = j.get("message", "")
            msg_lower = msg.lower()

            if "got" in msg_lower:
                ok += 1
                points = j.get("points", "-")
                status = "✅ 成功"
            elif "repeat" in msg_lower or "already" in msg_lower:
                repeat += 1
                status = "🔁 已签到"
            else:
                fail += 1
                status = "❌ 失败"

            # 状态接口（允许失败）
            s = scraper.get(STATUS_URL, headers=headers, timeout=TIMEOUT)
            sj = safe_json(s).get("data") or {}
            email = sj.get("email", email)
            if sj.get("leftDays") is not None:
                days = f"{int(float(sj['leftDays']))} 天"

        except Exception as e:
            fail += 1
            status = f"❌ 异常: {e}" # 打印具体的异常信息便于调试

        lines.append(f"{idx}. {email} | {status} | P:{points} | 剩余:{days}")
        # 增加随机延迟，模拟人类行为，减少被封禁的风险
        time.sleep(random.uniform(2, 5))

    title = f"GLaDOS 签到完成 ✅{ok} ❌{fail} 🔁{repeat}"
    content = "\n".join(lines)

    print(content)
    push(sckey, title, content)


if __name__ == "__main__":
    main()
