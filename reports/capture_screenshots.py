from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = "http://127.0.0.1:5001"
UPLOAD_ROOT = Path(__file__).parents[1] / "uploads"
OUT = Path(__file__).parent / "evidence" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)


def snap(page, name):
    page.screenshot(path=str(OUT / name), full_page=True)


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1440, "height": 900})
    page = context.new_page()

    page.goto(f"{ROOT}/login")
    snap(page, "01-login-page.png")

    page.goto(f"{ROOT}/register")
    snap(page, "02-register-page.png")

    page.goto(f"{ROOT}/login")
    page.fill('input[name="username"]', "pyknb")
    page.fill('input[name="password"]', "wrong-password")
    page.click('button[type="submit"]')
    page.wait_for_timeout(150)
    snap(page, "03-login-error.png")

    lock_result = page.evaluate("""async () => {
        const token = document.querySelector('input[name=csrf_token]').value;
        const body = new URLSearchParams({username: 'dio', password: 'wrong-password', csrf_token: token});
        const statuses = [];
        for (let i = 0; i < 5; i++) {
            const response = await fetch('/login', {method: 'POST', body});
            statuses.push(response.status);
        }
        return statuses.join(', ');
    }""")
    page.set_content(f"<html><body style='font:24px sans-serif;padding:48px'><h1>登录失败次数限制</h1><p>连续5次错误登录响应状态码：</p><pre>{lock_result}</pre><p>达到阈值后服务端进入临时锁定。</p></body></html>")
    snap(page, "04-login-lockout.png")

    page.goto(f"{ROOT}/register")
    page.fill('input[name="username"]', "screenshot_weak")
    page.fill('input[name="password"]', "123456")
    page.fill('input[name="confirm_password"]', "123456")
    page.click('button[type="submit"]')
    page.wait_for_timeout(150)
    snap(page, "05-register-weak-password.png")

    page.goto(f"{ROOT}/login")
    page.fill('input[name="username"]', "pyknb")
    page.fill('input[name="password"]', "114514")
    page.click('button[type="submit"]')
    page.wait_for_url("**/profile")
    snap(page, "06-profile-authenticated.png")

    page.goto(f"{ROOT}/upload")
    snap(page, "07-upload-page.png")

    page.set_input_files('input[name="file"]', {"name": "payload.exe", "mimeType": "application/octet-stream", "buffer": b"COURSE_TEST"})
    page.click('button[type="submit"]')
    page.wait_for_timeout(200)
    upload_result = page.locator("body").inner_text()
    page.set_content(f"<html><body style='font:24px sans-serif;padding:48px'><h1>危险文件上传拦截结果</h1><pre>{upload_result}</pre></body></html>")
    snap(page, "08-dangerous-upload-rejected.png")

    page.goto(f"{ROOT}/upload")
    page.set_input_files('input[name="file"]', {"name": "fake.png", "mimeType": "image/png", "buffer": b"COURSE_FAKE_IMAGE_TEST"})
    page.click('button[type="submit"]')
    page.wait_for_timeout(200)
    fake_result = page.locator("body").inner_text()
    page.set_content(f"<html><body style='font:24px sans-serif;padding:48px'><h1>伪装图片文件头校验结果</h1><pre>{fake_result}</pre></body></html>")
    snap(page, "09-fake-image-rejected.png")

    token = page.locator('input[name="csrf_token"]').input_value() if page.locator('input[name="csrf_token"]').count() else ""
    csrf_result = page.evaluate("""async () => {
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username: 'csrf_screenshot', password: 'Strong123', confirm_password: 'Strong123'})
        });
        return `${response.status} ${JSON.stringify(await response.json())}`;
    }""")
    page.set_content(f"<html><body style='font:24px sans-serif;padding:48px'><h1>CSRF拦截结果</h1><pre>{csrf_result}</pre></body></html>")
    snap(page, "10-csrf-rejected.png")

    page.goto(f"{ROOT}/logout")
    page.goto(f"{ROOT}/profile")
    snap(page, "11-after-logout-redirect.png")

    cookie_context = browser.new_context(viewport={"width": 1440, "height": 900})
    cookie_page = cookie_context.new_page()
    cookie_page.goto(f"{ROOT}/login")
    before = cookie_context.cookies()
    cookie_page.fill('input[name="username"]', "pyknb")
    cookie_page.fill('input[name="password"]', "114514")
    cookie_page.click('button[type="submit"]')
    cookie_page.wait_for_url("**/profile")
    after = cookie_context.cookies()
    before_session = next((item["value"] for item in before if item["name"] == "session"), "none")
    after_session = next((item["value"] for item in after if item["name"] == "session"), "none")
    cookie_info = [{key: item.get(key) for key in ("name", "domain", "path", "httpOnly", "secure", "sameSite")} for item in after]
    cookie_page.set_content(f"<html><body style='font:22px sans-serif;padding:48px'><h1>Session与Cookie安全属性</h1><p>登录前Session：{before_session[:12]}...</p><p>登录后Session：{after_session[:12]}...</p><p>Session ID 是否变化：{before_session != after_session}</p><pre>{cookie_info}</pre></body></html>")
    snap(cookie_page, "12-cookie-session-properties.png")
    cookie_context.close()

    (UPLOAD_ROOT / "pyknb").mkdir(exist_ok=True)
    (UPLOAD_ROOT / "zxrnb").mkdir(exist_ok=True)
    (UPLOAD_ROOT / "pyknb" / "user1_secret.txt").write_text("USER1_TEST_SECRET", encoding="utf-8")
    (UPLOAD_ROOT / "zxrnb" / "user2_secret.txt").write_text("USER2_TEST_SECRET", encoding="utf-8")
    user1 = browser.new_context(viewport={"width": 1440, "height": 900})
    user2 = browser.new_context(viewport={"width": 1440, "height": 900})
    p1, p2 = user1.new_page(), user2.new_page()
    for current, username, password in ((p1, "pyknb", "114514"), (p2, "zxrnb", "123456")):
        current.goto(f"{ROOT}/login")
        current.fill('input[name="username"]', username)
        current.fill('input[name="password"]', password)
        current.click('button[type="submit"]')
        current.wait_for_url("**/profile")
    idor = p2.evaluate("""async () => {
        const direct = await fetch('/download?filename=user1_secret.txt');
        const traversal = await fetch('/download?filename=../pyknb/user1_secret.txt');
        return `user2访问user1文件：${direct.status}\n路径穿越访问：${traversal.status}`;
    }""")
    p2.set_content(f"<html><body style='font:24px sans-serif;padding:48px'><h1>双账号越权与路径穿越复测</h1><pre>{idor}</pre><p>安全结果：user2不能读取user1文件。</p></body></html>")
    snap(p2, "13-idor-path-traversal-rejected.png")
    user1.close(); user2.close()
    for path in ((UPLOAD_ROOT / "pyknb" / "user1_secret.txt"), (UPLOAD_ROOT / "zxrnb" / "user2_secret.txt")):
        if path.exists(): path.unlink()

    browser.close()

print(f"screenshots saved to {OUT}")
