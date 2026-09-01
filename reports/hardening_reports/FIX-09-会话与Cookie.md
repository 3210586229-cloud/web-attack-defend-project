# FIX-09 会话与Cookie加固
## 1. 基本信息
- 类型：Session/Cookie；修复时间：2026-08-30；对应：VULN-09。
## 2. 根因定位
- 文件：`gets.py`；原风险为会话生命周期和 Cookie 属性缺少显式配置。
## 3. 修复措施
- HttpOnly、SameSite=Lax、可选 Secure；登录成功前清理旧 Session 并重建 CSRF 状态；退出 `session.clear()`；核心接口认证。
## 4. 验证
- 登录前后 Session 值变化；退出后 API 返回401；截图：`12-cookie-session-properties.png`、`11-after-logout-redirect.png`；外部证据归档于 `evidence/task9/`。
## 5. 残留
- 本地 HTTP 下 Secure=false；HTTPS 部署必须设置 `FLASK_COOKIE_SECURE=1`。
