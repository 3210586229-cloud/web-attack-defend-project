# -*- coding: utf-8 -*-
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = "http://127.0.0.1:5001"
OUT = Path(__file__).parent / "evidence" / "task_screens"
OUT.mkdir(parents=True, exist_ok=True)

def save(page, folder, number, name):
    page.screenshot(path=str(folder / f"{number:02d}-{name}.png"), full_page=True)

def do_login(page, user="pyknb", password="114514"):
    page.goto(ROOT + "/login")
    page.fill('input[name="username"]', user)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_timeout(150)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    for task in range(1, 10):
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        folder = OUT / f"task-{task:02d}"
        folder.mkdir(exist_ok=True)
        for old in folder.glob("*.png"):
            old.unlink()
        if task == 1:
            page.goto(ROOT + "/login"); save(page, folder, 1, "login")
            page.goto(ROOT + "/register"); page.fill('input[name="username"]', "weak-proof"); page.fill('input[name="password"]', "123456"); page.fill('input[name="confirm_password"]', "123456"); page.click('button[type="submit"]'); page.wait_for_timeout(120); save(page, folder, 2, "weak-password-rejected")
            page.goto(ROOT + "/login"); page.fill('input[name="username"]', "pyknb"); page.fill('input[name="password"]', "wrong-password"); page.click('button[type="submit"]'); page.wait_for_timeout(120); save(page, folder, 3, "wrong-password")
            for _ in range(5):
                page.goto(ROOT + "/login"); page.fill('input[name="username"]', "dio"); page.fill('input[name="password"]', "wrong-password"); page.click('button[type="submit"]'); page.wait_for_timeout(60)
            save(page, folder, 4, "lockout")
        elif task == 2:
            page.goto(ROOT + "/login"); page.fill('input[name="username"]', "' OR '1'='1"); page.fill('input[name="password"]', "' OR '1'='1"); page.click('button[type="submit"]'); page.wait_for_timeout(120); save(page, folder, 1, "sqli-login")
            page.goto(ROOT + "/register"); page.fill('input[name="username"]', "' OR '1'='1"); page.fill('input[name="password"]', "Strong123"); page.fill('input[name="confirm_password"]', "Strong123"); page.click('button[type="submit"]'); page.wait_for_timeout(120); save(page, folder, 2, "sqli-register")
            page.goto(ROOT + "/api/csrf"); save(page, folder, 3, "api-response")
            page.goto(ROOT + "/login"); save(page, folder, 4, "parameter-input")
        elif task == 3:
            do_login(page); page.goto(ROOT + "/listfiles"); save(page, folder, 1, "file-list")
            page.goto(ROOT + "/upload"); page.set_input_files('input[name="file"]', {"name": "xss.png", "mimeType": "image/png", "buffer": bytes([137,80,78,71,13,10,26,10])}); page.fill('#customName', '<script>alert(1)</script>.png'); page.click('button[type="submit"]'); page.wait_for_timeout(120); page.goto(ROOT + "/listfiles"); save(page, folder, 2, "escaped-filename")
            page.goto(ROOT + "/login?name=%3Cscript%3Ealert(1)%3C/script%3E"); save(page, folder, 3, "escaped-login")
            page.goto(ROOT + "/register?name=%3Cscript%3Ealert(1)%3C/script%3E"); save(page, folder, 4, "escaped-register")
        elif task == 4:
            page.goto(ROOT + "/register"); save(page, folder, 1, "csrf-form")
            page.route("**/register", lambda route: route.continue_(post_data="username=csrf-proof&password=Strong123&confirm_password=Strong123"))
            page.fill('input[name="username"]', "csrf-proof"); page.fill('input[name="password"]', "Strong123"); page.fill('input[name="confirm_password"]', "Strong123"); page.click('button[type="submit"]'); page.wait_for_timeout(120); save(page, folder, 2, "csrf-rejected")
            page.unroute("**/register"); do_login(page); page.goto(ROOT + "/upload"); save(page, folder, 3, "upload-csrf")
            page.goto(ROOT + "/api/csrf"); save(page, folder, 4, "csrf-token")
        elif task == 5:
            do_login(page, "zxrnb", "123456"); page.goto(ROOT + "/listfiles"); save(page, folder, 1, "own-files")
            page.goto(ROOT + "/download?filename=../pyknb/user1_secret.txt"); save(page, folder, 2, "traversal-rejected")
            page.goto(ROOT + "/download?filename=user1_secret.txt"); save(page, folder, 3, "cross-user-rejected")
            page.goto(ROOT + "/api/files"); save(page, folder, 4, "scoped-api")
        elif task == 6:
            do_login(page); page.goto(ROOT + "/upload"); save(page, folder, 1, "upload-form")
            page.set_input_files('input[name="file"]', {"name": "payload.exe", "mimeType": "application/octet-stream", "buffer": b"COURSE_TEST"}); page.click('button[type="submit"]'); page.wait_for_timeout(120); save(page, folder, 2, "exe-rejected")
            page.goto(ROOT + "/upload"); page.set_input_files('input[name="file"]', {"name": "fake.png", "mimeType": "image/png", "buffer": b"not-an-image"}); page.click('button[type="submit"]'); page.wait_for_timeout(120); save(page, folder, 3, "fake-png-rejected")
            page.goto(ROOT + "/listfiles"); save(page, folder, 4, "files-after-test")
        elif task == 7:
            page.goto(ROOT + "/?name={{7*7}}"); save(page, folder, 1, "ssti-index")
            page.goto(ROOT + "/login?name={{7*7}}"); save(page, folder, 2, "ssti-login")
            page.goto(ROOT + "/register?name={{7*7}}"); save(page, folder, 3, "ssti-register")
            page.goto(ROOT + "/login"); page.fill('input[name="username"]', "{{7*7}}"); page.fill('input[name="password"]', "{{7*7}}"); page.click('button[type="submit"]'); page.wait_for_timeout(120); save(page, folder, 4, "ssti-login-result")
        elif task == 8:
            page.goto(ROOT + "/"); save(page, folder, 1, "index-surface")
            page.goto(ROOT + "/login"); save(page, folder, 2, "login-surface")
            page.goto(ROOT + "/register"); save(page, folder, 3, "register-surface")
            do_login(page); page.goto(ROOT + "/upload"); save(page, folder, 4, "upload-surface")
        else:
            page.goto(ROOT + "/login"); save(page, folder, 1, "before-login")
            do_login(page); save(page, folder, 2, "profile-session")
            page.goto(ROOT + "/listfiles"); save(page, folder, 3, "files-session")
            page.goto(ROOT + "/logout"); page.goto(ROOT + "/profile"); save(page, folder, 4, "after-logout")
        context.close()
    browser.close()
print("saved 36 task-specific screenshots")
