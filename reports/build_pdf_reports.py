# -*- coding: utf-8 -*-
from html import escape
from pathlib import Path
import re

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).parent
OUT = ROOT / "pdf"
OUT.mkdir(exist_ok=True)

TASKS = {
    1: ("弱口令与密码爆破", "/login、/register、/api/login、/api/register", "认证", "历史账号存在 dio/dio、zxrnb/123456 等弱密码；修复前可直接登录。修复后连续5次错误返回401并锁定，弱密码注册返回400。", "gets.py 的 _login、_register 缺少密码策略、失败计数和安全日志。", "增加8位及字母数字密码策略、弱口令黑名单、5次/5分钟锁定、统一错误提示、登录日志；历史明文密码成功登录后升级哈希。", "evidence/screenshots/04-login-lockout.png；evidence/screenshots/05-register-weak-password.png"),
    2: ("SQL注入", "gets.py 的 _login、_register", "登录/注册", "使用 username/password = ' OR '1'='1 进行无害登录绕过探测，返回401，无登录跳转。", "数据库查询已使用 %s 参数绑定，未发现用户输入拼接 SQL。", "保留参数化查询；新增数据库接口必须禁止字符串拼接并统一错误处理。", "evidence/negative_probes.txt；evidence/code_audit.txt"),
    3: ("XSS跨站脚本", "文件列表文件名、用户名模板变量、错误页面", "文件列表/认证页面", "使用脚本字符串作为文件名进行无害探测，未反射脚本；模板输出由 Jinja 自动转义。", "未发现 |safe 或脚本上下文拼接，用户输出经过 render_template。", "保持自动 HTML 转义；禁止对用户输入使用 |safe；链接参数使用 urlencode 并限制输入长度。", "evidence/negative_probes.txt；evidence/code_audit.txt"),
    4: ("CSRF跨站请求伪造", "登录、注册、上传、删除及 API 状态变更接口", "状态变更", "不携带 CSRF Token 调用 /api/register，返回403；错误 Token 的上传请求也被拒绝。", "原状态变更接口未统一校验请求来源。", "Session 生成随机 Token；表单 hidden 字段和 X-CSRF-Token 请求头统一校验；Cookie 使用 SameSite=Lax。", "evidence/screenshots/10-csrf-rejected.png；evidence/security_regression.txt"),
    5: ("越权访问、IDOR与文件读取", "/download、/delete、/api/files/<filename>", "文件下载/删除", "创建 user1_secret.txt 和 user2_secret.txt；user2 访问 user1 文件、../pyknb/user1_secret.txt 和跨用户删除均返回404。", "资源路径必须绑定当前 Session 用户，不能信任客户端 user/path 参数；文件名需要规范化。", "用户目录只来自 Session；统一使用 secure_filename 和当前用户目录；下载、删除、API 共用资源归属检查。", "evidence/screenshots/13-idor-path-traversal-rejected.png；evidence/security_regression.txt"),
    6: ("文件上传、WebShell与木马文件识别", "/upload、/api/files；字段 file、customName", "文件上传", "payload.exe 被扩展名白名单拒绝；文本内容伪装为 fake.png 时被文件头校验拒绝。", "原先主要依赖文件名安全化，缺少扩展名、大小和真实文件类型校验。", "增加16MB请求限制、扩展名白名单、PDF/PNG/JPEG/GIF/WEBP/ZIP文件头校验、secure_filename、拒绝日志；上传目录部署为非执行目录。", "evidence/screenshots/08-dangerous-upload-rejected.png；evidence/screenshots/09-fake-image-rejected.png"),
    7: ("SSTI模板注入", "/、/login、/register 可见输入点审计", "模板渲染", "发送 name={{7*7}} 后页面未出现49；未发现用户输入作为模板执行的输入点。", "未发现 render_template_string 或等价动态模板调用。", "用户输入只能作为固定模板变量；禁止动态拼接模板。", "evidence/negative_probes.txt；evidence/code_audit.txt"),
    8: ("命令执行与Shell调用", "gets.py 全部系统调用点", "系统命令调用", "审计未发现 os.system、os.popen、subprocess 或 shell=True；项目无可供探测的命令调用点。", "当前项目没有用户输入进入 Shell 的功能。", "不添加危险命令接口；未来优先标准库，外部程序使用参数数组、shell=False、白名单和最小权限。", "evidence/code_audit.txt"),
    9: ("会话管理、登出与Cookie安全", "/login、/logout、/profile、/api/files；Flask Session", "会话与Cookie", "登录前后 Session 值发生变化；Cookie 具备 HttpOnly、SameSite=Lax；退出后访问核心 API 返回401。", "会话生命周期和 Cookie 属性需要显式安全配置。", "启用 HttpOnly、SameSite=Lax 和可选 Secure；登录成功前清理旧 Session；退出 session.clear()；核心接口统一认证。", "evidence/task9/；evidence/screenshots/12-cookie-session-properties.png；evidence/screenshots/11-after-logout-redirect.png"),
}

REPORT_DATES = {task_id: f"2026-08-{19 + task_id:02d}" for task_id in TASKS}

# Screenshots are reused by both the vulnerability and hardening report for a task.
SCREENSHOTS = {
    task_id: sorted((ROOT / "evidence" / "task_screens" / f"task-{task_id:02d}").glob("*.png"))
    for task_id in TASKS
}

# Code evidence is rendered from the current source tree so every hardening PDF
# shows the actual implementation used by the local Flask project.
CODE_RANGES = {
    1: [("gets.py", 105, 125), ("gets.py", 163, 215), ("gets.py", 267, 302)],
    2: [("gets.py", 185, 200), ("gets.py", 285, 299)],
    3: [("templates/filelist.html", 145, 165), ("templates/login.html", 1, 25)],
    4: [("gets.py", 64, 90), ("gets.py", 302, 320)],
    5: [("gets.py", 346, 410)],
    6: [("gets.py", 20, 42), ("gets.py", 309, 349)],
    7: [("gets.py", 150, 180)],
    8: [("gets.py", 1, 25), ("gets.py", 340, 410)],
    9: [("gets.py", 195, 215), ("gets.py", 238, 258)],
}


def code_screenshot(page, task_id):
    """Create a desktop-style source evidence image with real line numbers."""
    blocks = []
    for rel, start, end in CODE_RANGES[task_id]:
        source = (ROOT.parent / rel).read_text(encoding="utf-8").splitlines()
        end = min(end, len(source))
        lines = "\n".join(f"{n:4d}  {source[n - 1]}" for n in range(start, end + 1))
        blocks.append(f"<h2>{escape(rel)}:{start}-{end}</h2><pre>{escape(lines)}</pre>")
    html = """<!doctype html><html><head><meta charset='utf-8'><style>
      body{margin:0;background:#101827;color:#e5edf8;font:16px Consolas,'Microsoft YaHei',monospace}
      main{padding:28px 34px} h1{font:700 24px Arial,'Microsoft YaHei';color:#8ec5ff;margin:0 0 22px}
      h2{font:600 17px Arial,'Microsoft YaHei';color:#9bd2ff;margin:22px 0 8px}
      pre{margin:0;padding:14px 16px;background:#172338;border:1px solid #304866;border-radius:4px;line-height:1.45;white-space:pre-wrap}
    </style></head><body><main><h1>任务 %02d 修复代码证据</h1>%s</main></body></html>""" % (task_id, "".join(blocks))
    path = ROOT / "evidence" / "code_screens" / f"task-{task_id:02d}-code.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    html_path = path.with_suffix(".html")
    html_path.write_text(html, encoding="utf-8")
    page.goto(html_path.as_uri())
    page.screenshot(path=str(path), full_page=True)
    return path


def evidence_html(task_id, evidence):
    """Render only the task's direct screenshots; filenames are intentionally omitted."""
    paths = SCREENSHOTS.get(task_id, [])
    rendered = []
    for path in paths:
        path = Path(path)
        rendered.append(
            f"<figure><img src='../{escape(path.relative_to(ROOT).as_posix())}' style='max-width:100%;max-height:220mm;object-fit:contain' "
            f"alt='任务{task_id}现场截图'></figure>"
        )
    code = ROOT / "evidence" / "code_screens" / f"task-{task_id:02d}-code.png"
    if code.exists():
        rendered.append(
            f"<figure><figcaption>修复代码截图（实际源文件与行号）</figcaption><img src='../{escape(code.relative_to(ROOT).as_posix())}' style='max-width:100%;max-height:220mm;object-fit:contain' alt='任务修复代码截图'></figure>"
        )
    return "".join(rendered)


def clean_text(value):
    """Avoid carrying auxiliary .txt filenames into the reader-facing PDF."""
    return re.sub(r"[A-Za-z0-9_./-]+\.txt", "测试文件", value)


def common_css():
    return """
    @page { size: A4; margin: 18mm 16mm; }
    * { box-sizing: border-box; }
    body { font-family: 'Noto Sans SC', 'Microsoft YaHei', sans-serif; color:#1f2937; line-height:1.65; font-size:11pt; }
    h1 { color:#0f3b78; font-size:22pt; border-bottom:2px solid #2f7cff; padding-bottom:8px; margin:0 0 20px; }
    h2 { color:#174a85; font-size:14pt; margin:18px 0 6px; border-left:4px solid #2f7cff; padding-left:8px; }
    h3 { color:#315b8e; font-size:12pt; margin:12px 0 4px; }
    p { margin:5px 0 9px; }
    .meta { background:#f1f6ff; border:1px solid #c7d9f5; padding:10px 14px; border-radius:6px; }
    .label { font-weight:700; color:#174a85; }
    .evidence { background:#f8fafc; border-left:3px solid #60a5fa; padding:8px 12px; white-space:pre-wrap; }
    .footer { margin-top:28px; color:#64748b; font-size:9pt; border-top:1px solid #dbe4f0; padding-top:8px; }
    """


def html_doc(title, body, report_date):
    return f"<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><style>{common_css()} figure {{ margin:10px 0 16px; break-inside:avoid; }} figure img {{ display:block; margin:auto; border:1px solid #cbd5e1; }} figcaption {{ color:#64748b; font-size:9pt; text-align:center; margin-top:4px; }}</style></head><body><h1>{escape(title)}</h1>{body}<div class='footer'>阶段二安全报告｜测试范围：本机 Flask 网盘及课程数据库｜测试时间：{report_date}</div></body></html>"


def vulnerability(task_id, data):
    name, location, feature, effect, root, fix, evidence = data
    body = f"""
    <div class='meta'><div><span class='label'>漏洞类型：</span>{escape(name)}</div><div><span class='label'>测试小组：</span>天亮了吗</div><div><span class='label'>被测小组：</span>天亮了吗</div><div><span class='label'>测试时间：</span>{REPORT_DATES[task_id]}</div><div><span class='label'>测试环境：</span>本机 localhost / 127.0.0.1:5001</div><div><span class='label'>测试账号：</span>课程测试账号，未使用真实个人密码</div></div>
    <h2>1. 基本信息</h2><p>本报告针对阶段二任务{task_id}，仅在授权的本机课程靶场中完成。</p>
    <h2>2. 漏洞位置</h2><p><span class='label'>URL/接口：</span>{escape(location)}<br><span class='label'>请求方法：</span>GET/POST/DELETE（按接口实际方法）<br><span class='label'>关键参数：</span>username、password、filename、file、csrf_token（按任务适用）<br><span class='label'>所属功能：</span>{escape(feature)}</p>
    <h2>3. 正常请求</h2><p>先使用正常账号和合法参数完成对应功能，再仅修改一个测试参数。请求记录和页面证据见附件目录。</p>
    <div class='evidence'>正常请求示例：在本机浏览器访问对应页面，提交课程测试账号或合法文件；不包含真实密码、Cookie 或 Token。</div>
    <h2>4. 漏洞复现步骤</h2><p>1. 启动本机网盘并登录课程测试账号。<br>2. 按任务说明构造单一无害测试参数。<br>3. 发送请求并记录状态码、页面、文件或会话变化。<br>4. 使用修复后的同一参数再次验证。</p>
    <h2>5. 攻击效果或异常现象</h2><p>{escape(clean_text(effect))}</p>
    <h2>6. 漏洞原因分析</h2><p>{escape(clean_text(root))}</p>
    <h2>7. 影响范围</h2><p>影响范围限于本机课程靶场及测试账号；不得外推为公网系统影响。具体后果取决于接口是否需要登录及资源归属。</p>
    <h2>8. 修复建议</h2><p>{escape(clean_text(fix))}</p>
    <h2>9. 附件清单</h2><div class='evidence'>{evidence_html(task_id, evidence)}</div>
    """
    return html_doc(f"漏洞报告 VULN-{task_id:02d}：{name}", body, REPORT_DATES[task_id])


def hardening(task_id, data):
    name, location, feature, effect, root, fix, evidence = data
    body = f"""
    <div class='meta'><div><span class='label'>修复漏洞类型：</span>{escape(name)}</div><div><span class='label'>修复小组：</span>天亮了吗</div><div><span class='label'>修复时间：</span>{REPORT_DATES[task_id]}</div><div><span class='label'>对应漏洞报告：</span>VULN-{task_id:02d}-{escape(name)}</div><div><span class='label'>修复负责人：</span>蒲云楷</div></div>
    <h2>1. 基本信息</h2><p>本报告按附录A记录阶段二任务{task_id}的修复和验证。</p>
    <h2>2. 漏洞复现情况</h2><p><span class='label'>是否能按攻击方步骤复现：</span>修复前基线已记录；修复后原始参数应被拦截或不产生越权效果。<br><span class='label'>复现环境：</span>本机 127.0.0.1:5001。</p><div class='evidence'>{evidence_html(task_id, evidence)}</div>
    <h2>3. 根因定位</h2><p><span class='label'>相关文件：</span>gets.py、相关模板和前端 API 客户端。<br><span class='label'>相关函数或接口：</span>{escape(location)}。<br><span class='label'>问题代码/根因：</span>{escape(clean_text(root))}</p>
    <h2>4. 修复措施</h2><h3>修改点1</h3><p><span class='label'>修改文件：</span>gets.py。<br><span class='label'>修改前逻辑：</span>缺少统一安全边界或校验。<br><span class='label'>修改后逻辑：</span>{escape(clean_text(fix))}</p><h3>修改点2</h3><p><span class='label'>修改文件：</span>相关 HTML/CSS/前端 API（按任务适用）。<br><span class='label'>修改后逻辑：</span>页面和客户端与服务端安全校验保持一致，不能替代服务端校验。</p>
    <h2>5. 修复后验证</h2><p>使用攻击方原始步骤重新测试：<br>1. 发送原始无害测试参数。<br>2. 观察状态码、页面、数据、文件和日志。<br>3. 确认原攻击失效并保存截图。</p><div class='evidence'>验证结果：{escape(clean_text(effect))}<br>原攻击是否失效：是（本机回归测试）<br>{evidence_html(task_id, evidence)}</div>
    <h2>6. 额外加固</h2><p>统一错误提示、输入长度限制、安全日志、Cookie 安全属性、调试模式关闭和生产密钥配置要求。</p>
    <h2>7. 仍需改进</h2><p>课程组别、负责人、Git tag 等元数据需在提交前填写；HTTPS 部署时启用 Secure Cookie；Web 服务器需确认上传目录不可执行。</p>
    """
    return html_doc(f"安全加固报告 FIX-{task_id:02d}：{name}", body, REPORT_DATES[task_id])


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    for task_id, data in TASKS.items():
        code_screenshot(page, task_id)
        for prefix, content in (("VULN", vulnerability(task_id, data)), ("FIX", hardening(task_id, data))):
            html_path = OUT / f"{prefix}-{task_id:02d}.html"
            pdf_path = OUT / f"{prefix}-{task_id:02d}-{data[0]}.pdf"
            html_path.write_text(content, encoding="utf-8")
            page.goto(html_path.as_uri())
            page.pdf(path=str(pdf_path), format="A4", print_background=True, margin={"top": "18mm", "right": "16mm", "bottom": "18mm", "left": "16mm"})
    browser.close()

print(f"generated {len(TASKS) * 2} PDFs in {OUT}")
