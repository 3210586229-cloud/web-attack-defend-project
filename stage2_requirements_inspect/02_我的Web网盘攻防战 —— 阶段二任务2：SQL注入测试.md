# 我的Web网盘攻防战 —— 阶段二任务2：SQL注入测试

## 写在前面：当用户输入变成了SQL的一部分

在开发登录功能时，我们为了后续攻防学习，曾经故意保留过一种危险写法：把用户输入直接拼接进 SQL 语句。现在就是验证它的时候。SQL注入的核心不是“某个神奇字符串”，而是程序把用户输入当成了SQL代码的一部分执行。当输入改变了原本的查询逻辑，就可能绕过登录、读取不该读取的数据，甚至修改数据。

> **边界提醒**：本任务只允许在自己小组的网盘靶场、课程指定互测靶场、虚拟机或本机 `localhost` 中完成。不要扫描、爆破、上传、探测任何未授权网站、校园系统、云服务或他人真实业务系统。所有攻击动作都必须可回滚、可截图、可复现，不以破坏数据为目标。

------

## 本次任务完成后，你将理解

- SQL语句拼接为什么危险；
- 登录绕过型SQL注入如何产生；
- 如何判断一个参数是否可能进入SQL查询；
- 如何通过错误回显、布尔差异、时间差异判断是否存在SQL注入风险；
- 如何在课程靶场中使用 sqlmap 做低风险、可控的自动化验证；
- 为什么前端过滤不是修复；
- 如何使用参数化查询修复漏洞。

------

## 任务总览

| 步骤  | 做什么                | 你能看到什么                         |
| ----- | --------------------- | ------------------------------------ |
| 第1步 | 找到可能进入SQL的参数 | 登录框、搜索框、文件查询接口         |
| 第2步 | 观察正常SQL逻辑       | 明白原本应该查什么                   |
| 第3步 | 做登录绕过测试        | 特殊输入让条件恒真                   |
| 第4步 | 做错误回显/布尔探测   | 判断是否存在SQL语义变化              |
| 第5步 | 使用 sqlmap 辅助验证  | 自动化确认注入点、注入参数和注入类型 |
| 第6步 | 参数化修复            | 同样输入不再改变SQL语义              |

------

## 第1步：找到可能进入SQL的参数

先不要急着输入payload。你要先列出哪些地方可能查询数据库：登录接口的 `username` / `email` / `password`，注册接口的用户名重复检查，文件搜索，文件详情，管理页面。对于基础网盘，最典型的是登录接口。

```http
POST /login HTTP/1.1
Content-Type: application/x-www-form-urlencoded

username=user1&password=123456
```

你要记录：请求方法、URL、参数名、正常登录成功和失败分别是什么页面。

### ✅ 第1步完成标志

- 至少列出 1 个可能进入数据库查询的接口；
- 能说明这个接口查询哪张表、用哪些字段判断；
- 保存一份正常请求截图或请求包。

------

## 第2步：理解漏洞代码长什么样

典型危险写法如下：

```java
String sql = "SELECT * FROM users WHERE username='" + username + "' AND password='" + password + "'";
```

或者 Python 中：

```python
sql = "SELECT * FROM users WHERE username='%s' AND password='%s'" % (username, password)
```

如果用户输入只是普通字符串，SQL看起来没问题：

```sql
SELECT * FROM users WHERE username='user1' AND password='123456'
```

但如果输入中包含引号、逻辑运算符、注释符，原本的SQL结构就可能被改变。SQL注入不是数据库“坏了”，也不是浏览器“坏了”，而是后端程序错误地把数据和代码混在了一起。

------

## 第3步：登录绕过测试

课程中建议只做登录绕过，不做破坏性操作。一个常见的课程演示输入是：

```text
用户名：user1
密码：' OR '1'='1
```

如果后端SQL是字符串拼接，可能变成类似：

```sql
SELECT * FROM users WHERE username='user1' AND password='' OR '1'='1'
```

这时 `OR '1'='1'` 恒为真，查询结果可能不再符合原本的“用户名和密码都正确”要求。不同数据库、不同拼接方式、不同字段位置，测试字符串可能不同。本任务不要求背payload，而要求你能解释为什么会改变SQL语义。

如果前端禁止输入空格、引号或把密码框隐藏了，这不代表系统安全。你可以用浏览器 F12 修改输入框属性，或用 Postman、Apifox、Burp、ZAP 等工具在授权靶场重放请求。前端过滤只能改善用户体验，不能作为安全边界。

### ✅ 第3步完成标志

- 成功或失败都要记录测试过程；
- 如果成功绕过，截图证明登录前后变化；
- 如果没有成功，说明你测试的参数、响应变化，以及是否可能已被参数化修复。

------

## 第4步：错误回显与布尔探测

如果登录绕过不明显，你还可以观察输入单引号后系统是否出现数据库错误，例如 SQL syntax error。页面直接暴露数据库错误，说明系统不仅可能有注入风险，还存在错误信息泄露。

也可以对同一参数分别输入“恒真”和“恒假”的条件，观察响应是否不同：

```text
' OR '1'='1
' OR '1'='2
```

如果两次响应明显不同，说明输入可能影响了SQL逻辑。基础任务不要求执行删除、修改、写文件、系统命令等破坏性动作。

------

## 第5步：推荐工具 sqlmap 的课程使用方式

### 5.1 sqlmap 是什么

`sqlmap` 是一个用于自动化检测 SQL 注入漏洞的安全测试工具。它可以帮助你完成下面几件事：

- 判断某个参数是否可能存在 SQL 注入；
- 判断注入大致属于哪一类，例如布尔盲注、报错注入、时间盲注等；
- 辅助确认数据库类型；
- 生成较清晰的测试过程输出，便于写报告。

但是，sqlmap 不是“万能漏洞扫描器”，也不是“自动攻击按钮”。它只是把手工测试中的很多探测动作自动化。你仍然要先理解：哪个接口可能查数据库、哪个参数进入了 SQL、正常响应和异常响应有什么区别。

> **课程限制**：本任务中 sqlmap 只允许用于检测和验证 SQL 注入点。不要使用 `--dump` 导出数据，不要使用 `--file-read` 读取服务器文件，不要使用 `--file-write` 写文件，不要使用 `--os-shell`、`--os-pwn` 或任何系统命令相关功能。你要证明“参数存在注入风险”，而不是破坏数据库或控制服务器。

------

### 5.2 使用 sqlmap 前要准备什么

在运行 sqlmap 之前，请先完成三件事。

第一，确认测试目标是课程靶场。例如：

```text
http://127.0.0.1:5000/login
http://localhost:8080/file/search
http://192.168.56.101:8080/login
```

第二，确认请求方法和参数。如果是 GET 请求，参数直接在 URL 中：

```text
http://127.0.0.1:5000/file/search?keyword=test
```

如果是 POST 请求，需要知道提交的数据格式：

```http
POST /login HTTP/1.1
Content-Type: application/x-www-form-urlencoded

username=user1&password=123456
```

第三，确认正常响应和失败响应。例如登录失败时页面中是否有：

```text
用户名或密码错误
login failed
invalid password
```

sqlmap 需要通过响应差异判断测试结果。如果你的系统所有响应都完全一样，或者需要验证码、CSRF Token、登录态 Cookie，sqlmap 的测试就需要额外配置。

------

### 5.3 安装与版本检查

如果你使用 Kali Linux，通常已经自带 sqlmap。可以先查看版本：

```bash
sqlmap --version
```

如果没有安装，可以在课程虚拟机中使用：

```bash
sudo apt update
sudo apt install sqlmap
```

也可以使用 Python 方式运行官方项目：

```bash
python3 sqlmap.py --version
```

不要求每位同学都安装到真实主机系统中。建议在课程虚拟机、Docker 环境或本机靶场环境中使用，便于控制影响范围。

------

### 5.4 对 GET 参数做低风险检测

假设你的网盘有文件搜索功能：

```text
http://127.0.0.1:5000/file/search?keyword=test
```

可以使用下面的低风险命令：

```bash
sqlmap -u "http://127.0.0.1:5000/file/search?keyword=test" -p keyword --batch --level=1 --risk=1 --threads=1 --delay=1
```

参数说明：

- `-u`：指定要测试的 URL；
- `-p keyword`：只测试 `keyword` 这个参数，不要让工具乱测无关参数；
- `--batch`：使用默认回答，避免交互式反复询问；
- `--level=1`：最低测试深度；
- `--risk=1`：最低风险等级；
- `--threads=1`：单线程，避免对课程靶场造成压力；
- `--delay=1`：每次请求之间等待 1 秒，降低请求频率。

如果 sqlmap 输出类似：

```text
Parameter: keyword (GET)
    Type: boolean-based blind
    Title: AND boolean-based blind - WHERE or HAVING clause
```

说明它认为 `keyword` 参数可能存在布尔盲注。你不能只截图这一行就结束，还要回到代码中找原因，说明后端是否把 `keyword` 拼接进了 SQL。

------

### 5.5 对 POST 登录接口做低风险检测

登录接口通常是 POST 请求，直接用 `-u` 不一定方便。更推荐先用 Burp、ZAP、浏览器开发者工具、Postman 或 Apifox 抓取一份完整请求，保存为 `login.txt`。

示例 `login.txt`：

```http
POST /login HTTP/1.1
Host: 127.0.0.1:5000
Content-Type: application/x-www-form-urlencoded

username=user1&password=123456
```

然后用 sqlmap 读取请求文件：

```bash
sqlmap -r login.txt -p username,password --batch --level=1 --risk=1 --threads=1 --delay=1
```

参数说明：

- `-r login.txt`：从文件中读取完整 HTTP 请求；
- `-p username,password`：只测试用户名和密码参数；
- `--batch`：自动选择默认选项；
- `--level=1 --risk=1`：只做低风险基础检测；
- `--threads=1 --delay=1`：低速测试，避免高频请求。

如果你的登录接口只想测试 `password` 参数，可以写成：

```bash
sqlmap -r login.txt -p password --batch --level=1 --risk=1 --threads=1 --delay=1
```

------

### 5.6 带 Cookie 的接口如何测试

有些文件搜索、文件详情、文件列表接口必须登录后才能访问。此时要带上课程测试账号的 Cookie。可以把完整请求保存为 `search.txt`：

```http
GET /file/search?keyword=test HTTP/1.1
Host: 127.0.0.1:5000
Cookie: session=课程测试账号自己的session
```

然后运行：

```bash
sqlmap -r search.txt -p keyword --batch --level=1 --risk=1 --threads=1 --delay=1
```

注意：只能使用你自己的课程测试账号 Cookie，不要使用同学真实账号，不要在报告里公开完整 Cookie。截图时可以把 Cookie 中间部分打码。

------

### 5.7 常见输出怎么看

sqlmap 常见输出中，你重点看三类信息。

第一类是是否发现注入：

```text
parameter 'keyword' appears to be injectable
```

这表示 sqlmap 判断该参数可能可注入。

第二类是注入类型：

```text
Type: boolean-based blind
Type: error-based
Type: time-based blind
```

含义如下：

- `boolean-based blind`：布尔盲注，页面不会直接报错，但真假条件导致响应差异；
- `error-based`：报错注入，数据库错误信息可能被页面返回；
- `time-based blind`：时间盲注，通过响应延迟判断 SQL 是否被执行；
- `UNION query`：联合查询注入，输入可能改变 SELECT 结果结构。

第三类是后端数据库信息：

```text
back-end DBMS: MySQL
back-end DBMS: SQLite
back-end DBMS: PostgreSQL
```

这类信息可以写进报告，但不要继续做数据导出。课程目标是确认漏洞、解释原理、完成修复。

------

### 5.8 常见问题排查

如果 sqlmap 没有发现注入，不代表一定没有漏洞。你需要排查下面几个问题：

1. 你测试的参数是否真的进入 SQL？
2. 请求方法是否正确？GET 和 POST 是否混淆？
3. 参数名是否写错？
4. 登录态 Cookie 是否过期？
5. 系统是否有 CSRF Token，导致重放请求失败？
6. 后端是否已经使用参数化查询？
7. 页面响应差异是否太小，工具难以判断？
8. 是否存在前端输入框限制，但后端其实没有限制？

如果接口需要 CSRF Token，课程基础任务不要求复杂自动化绕过。你可以改用手工测试，或者在报告中说明“该接口存在动态 Token，sqlmap 直接重放失败，因此采用手工布尔差异测试”。

------

### 5.9 本任务禁止使用的 sqlmap 参数

为了保证课程测试可控，本任务不要使用下面这些参数：

```text
--dump
--dump-all
--file-read
--file-write
--file-dest
--os-shell
--os-pwn
--os-cmd
--priv-esc
--risk=3
--level=5
--threads=10
```

原因很简单：这些参数可能造成数据导出、文件读写、系统命令执行或高强度请求，不适合本阶段课程任务。你们现在要学习的是“发现问题—解释原因—完成修复”，不是比谁能把数据库导出来。

------

### 5.10 sqlmap 测试记录应该怎么写进报告

报告中不要只写：

```text
使用 sqlmap 扫描，发现 SQL 注入。
```

应该写清楚：

```text
测试工具：sqlmap
测试范围：本组课程靶场 http://127.0.0.1:5000/file/search
测试参数：keyword
测试命令：sqlmap -u "http://127.0.0.1:5000/file/search?keyword=test" -p keyword --batch --level=1 --risk=1 --threads=1 --delay=1
测试结果：sqlmap 判断 keyword 参数存在 boolean-based blind 类型注入风险
人工复核：分别输入恒真条件与恒假条件后，页面响应存在明显差异
根因分析：后端将 keyword 直接拼接进 SELECT 查询语句
修复方式：改为参数化查询
修复验证：再次运行相同命令，未发现 keyword 参数可注入；手工恒真/恒假输入也不再造成响应差异
```

------

### ✅ 第5步完成标志

- 至少使用 sqlmap 对 1 个课程靶场接口做低风险检测；
- 命令中包含 `--level=1 --risk=1 --threads=1`；
- 能解释 `-u`、`-r`、`-p`、`--batch` 的含义；
- 能说明 sqlmap 输出中的注入参数、注入类型和数据库类型；
- 没有使用数据导出、文件读写、系统命令执行类参数；
- 能用手工方式复核 sqlmap 的结论。

------

## 第6步：使用参数化查询修复

修复SQL注入的核心是把SQL模板和用户数据分开。用户输入只能作为值，不允许成为SQL语法的一部分。

Java JDBC 安全写法：

```java
String sql = "SELECT * FROM users WHERE username=? AND password=?";
PreparedStatement ps = conn.prepareStatement(sql);
ps.setString(1, username);
ps.setString(2, password);
ResultSet rs = ps.executeQuery();
```

Python 安全写法：

```python
sql = "SELECT * FROM users WHERE username=%s AND password=%s"
cursor.execute(sql, (username, password))
```

SQLite 常见写法：

```python
sql = "SELECT * FROM users WHERE username=? AND password=?"
cursor.execute(sql, (username, password))
```

文件搜索接口也要参数化，不要以为只有登录接口会出问题。

危险写法：

```python
keyword = request.args.get("keyword")
sql = "SELECT * FROM files WHERE filename LIKE '%" + keyword + "%'"
cursor.execute(sql)
```

安全写法：

```python
keyword = request.args.get("keyword")
sql = "SELECT * FROM files WHERE filename LIKE ?"
cursor.execute(sql, ("%" + keyword + "%",))
```

不同数据库驱动的占位符可能不同，例如 SQLite 常用 `?`。同时不要把数据库错误直接返回给用户；登录失败统一提示；对输入长度做合理限制；数据库账号最小权限，不要让Web应用使用root账号连接数据库。

------

## 🤖 AI使用建议

- “请用大一学生能理解的话解释SQL注入中‘数据和代码混淆’是什么意思。”
- “下面是我的登录SQL拼接代码，请帮我改成参数化查询。”
- “为什么前端过滤单引号不能真正修复SQL注入？”
- “我的SQL注入测试没有成功，请帮我分析可能是参数位置、数据库语法还是代码已经修复。”
- “请解释 sqlmap 中 `-u`、`-r`、`-p`、`--batch`、`--level`、`--risk` 的含义。”
- “下面是 sqlmap 的输出，请帮我判断它发现的是哪一种 SQL 注入，并说明应该如何人工复核。”
- “请帮我把 sqlmap 测试结果整理成课程漏洞报告，不要夸大影响。”

## ✅ 本任务完成标志

- 找到至少一个可能进入SQL查询的参数；
- 能复现登录绕过、错误回显或布尔响应差异中的至少一种；
- 能使用 sqlmap 对课程靶场进行低风险辅助验证；
- 能说明 sqlmap 的测试参数、注入类型和输出含义；
- 能画出“用户输入 → SQL拼接 → 数据库执行 → 响应变化”的流程；
- 使用参数化查询完成修复；
- 修复后，原测试输入只被当成普通字符串，不再绕过登录；
- 修复后，再次使用原手工输入或 sqlmap 低风险命令进行验证，确认漏洞不再复现。

### 漏洞报告至少写清楚

- 漏洞类型：例如 SQL注入 / XSS / CSRF / 越权下载。
- 漏洞位置：完整 URL、接口路径、请求方法、关键参数。
- 测试环境：本机、虚拟机或课程互测靶场；测试时间；测试账号。
- 使用工具：是否使用 sqlmap；如果使用，要写清楚命令、参数、测试范围和低风险设置。
- 复现步骤：从登录、构造请求到观察结果，每一步都要截图或保存请求包。
- 影响说明：能造成什么后果，不能夸大；例如“可绕过登录进入文件列表”，不要写成“可控制服务器”。
- 修复建议：说明根因、给出修复方式，并附修复后同样步骤无法成功的证明。

### 修复时的共同原则

1. 不要只在前端过滤。浏览器里的限制都可以被 F12、代理工具或脚本绕过，后端必须做真正校验。
2. 不要只黑名单过滤某几个字符。优先采用白名单、参数化查询、框架内置安全机制、权限统一拦截。
3. 不要修一个接口漏一个接口。文件展示、下载、删除、重命名、分享等同类接口都要统一检查。
4. 修复后一定要用“原来的攻击参数”再测一遍，证明漏洞确实失效。
5. 工具结果不能代替人工分析。sqlmap 说“可能存在注入”之后，你还要解释代码根因；sqlmap 没扫出来，也不能直接证明系统一定安全。

## 最后的提醒

SQL注入的payload会变，工具也会变，但根因不变：不要让用户输入变成SQL代码。sqlmap 可以帮你更快发现问题，但真正重要的是你能解释为什么这个参数会影响 SQL 语义，以及如何用参数化查询让用户输入重新变回普通数据。只要你记住“参数化查询是正解”，以后遇到登录、搜索、详情查询、分页查询，都能用同一套思路检查。
