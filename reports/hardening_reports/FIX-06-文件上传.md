# FIX-06 文件上传加固
## 1. 基本信息
- 类型：文件上传；修复时间：2026-08-30；对应：VULN-06。
## 2. 根因定位
- 文件：`gets.py`；函数：`_save_upload`；原先仅安全化文件名，缺少类型和大小校验。
## 3. 修复措施
- 16MB请求限制；扩展名白名单；PDF、PNG、JPEG、GIF、WEBP、ZIP 文件头签名校验；安全文件名；拒绝日志；上传目录非执行部署要求。
## 4. 验证
- `.exe` 和文本伪装 `.png` 均返回400；截图：`evidence/screenshots/08-dangerous-upload-rejected.png`、`09-fake-image-rejected.png`。
## 5. 残留
- 反向代理/Web服务器需补上传目录不可执行配置和内容杀毒扫描。
