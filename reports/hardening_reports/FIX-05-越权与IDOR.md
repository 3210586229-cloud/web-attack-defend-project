# FIX-05 越权与IDOR加固
## 1. 基本信息
- 类型：水平越权/路径穿越；修复时间：2026-08-30；对应：VULN-05。
## 2. 根因定位
- 文件：`gets.py`；函数：`safe_user_file`；风险边界为身份来源、资源归属和路径拼接。
## 3. 修复措施
- 用户目录只来自 Session；文件名经 `secure_filename`；下载/删除/API 共用归属目录。
## 4. 验证
- user2 访问 user1 文件、`../` 路径和跨用户删除均404；截图：`evidence/screenshots/13-idor-path-traversal-rejected.png`。
## 5. 残留
- 新增分享、重命名、预览接口需复用归属检查。
