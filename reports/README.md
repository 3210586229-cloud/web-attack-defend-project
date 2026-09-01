# 阶段二安全加固报告包

本目录按阶段二9项任务组织。测试范围为本机 Flask 网盘和课程数据库 `account_id`，所有验证均使用无害参数和测试账号。

## 当前加固状态

| 任务 | 代码审计/加固结论 | 复测证据 |
| --- | --- | --- |
| 1 弱口令与爆破 | 已增加密码策略、5次失败锁定、统一提示、登录日志；历史明文密码成功登录后升级哈希 | `evidence/security_regression.txt` |
| 2 SQL注入 | 登录、注册查询使用参数化 SQL，未发现字符串拼接 SQL | `evidence/code_audit.txt` |
| 3 XSS | Jinja 模板默认转义；文件名链接使用 URL 编码；继续限制上传文件名 | `evidence/code_audit.txt` |
| 4 CSRF | 表单和 API 使用服务端 Token；状态变更接口拒绝缺少/错误 Token | `evidence/security_regression.txt` |
| 5 越权/IDOR | 文件路径绑定当前 Session 用户目录，并统一规范化文件名 | `evidence/code_audit.txt` |
| 6 文件上传 | 16MB 总大小限制、扩展名白名单、安全文件名 | `evidence/security_regression.txt` |
| 7 SSTI | 未发现 `render_template_string` 或用户输入模板执行点 | `evidence/code_audit.txt` |
| 8 命令执行 | 未发现 `os.system`、`subprocess`、`shell=True` 调用，完成代码审计结论 | `evidence/code_audit.txt` |
| 9 会话/Cookie | HttpOnly、SameSite=Lax、可选 Secure；登录清理并重新生成 Session，退出清理服务端状态 | `evidence/security_regression.txt` |

`vulnerability_reports/` 和 `hardening_reports/` 目前是报告索引，尚未替代9项独立的附录A报告。运行截图、浏览器 Cookie 面板截图、双账号越权证据和课程组别信息仍需在最终提交前补入 `evidence/`。详细缺口见 `最终完成性复核.md`。

已生成18份独立PDF（每项任务分别一份漏洞报告和一份安全加固报告），见 `pdf/`；PDF生成脚本为 `build_pdf_reports.py`。
