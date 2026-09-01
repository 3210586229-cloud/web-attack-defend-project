# FIX-07 SSTI加固
## 1. 基本信息
- 类型：SSTI；修复时间：2026-08-30；对应：VULN-07。
## 2. 根因定位
- 审计 `gets.py` 和模板，未发现动态模板执行调用。
## 3. 修复措施
- 规定用户输入只能作为固定模板变量，禁止 `render_template_string(user_input)`。
## 4. 验证
- 未发现可用输入点；审计证据：`evidence/code_audit.txt`。
