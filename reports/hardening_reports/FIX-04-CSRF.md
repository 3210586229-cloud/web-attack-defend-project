# FIX-04 CSRF加固
## 1. 基本信息
- 类型：CSRF；修复时间：2026-08-30；对应：VULN-04。
## 2. 根因定位
- 文件：`gets.py`；原状态变更接口未统一校验 Token。
## 3. 修复措施
- Session 随机 Token；表单 hidden 字段；API `X-CSRF-Token`；`compare_digest`；SameSite=Lax。
## 4. 验证
- 缺少 Token 的注册请求返回403；截图：`evidence/screenshots/10-csrf-rejected.png`。
## 5. 残留
- 新增状态变更接口必须使用同一装饰器/校验逻辑。
