import logging
import os
import secrets
import time
from functools import wraps

import pymysql
from flask import (
    Flask,
    abort,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("FLASK_COOKIE_SECURE", "0") == "1",
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,
)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
security_logger = logging.getLogger("webdrive.security")

db_config = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", "pyk114514"),
    "database": os.environ.get("DB_NAME", "account_id"),
    "charset": "utf8mb4",
}
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

LOGIN_MAX_FAILURES = 5
LOGIN_LOCK_SECONDS = 5 * 60
login_failures = {}
WEAK_PASSWORDS = {"123456", "12345678", "password", "admin", "admin123", "qwerty", "111111", "abc123", "114514", "123", "1919", "dio", "jojo"}
ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg", "gif", "webp", "zip", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "mp4"}
FILE_SIGNATURES = {
    "pdf": (b"%PDF-",),
    "png": (b"\x89PNG\r\n\x1a\n",),
    "jpg": (b"\xff\xd8\xff",),
    "jpeg": (b"\xff\xd8\xff",),
    "gif": (b"GIF87a", b"GIF89a"),
    "webp": (b"RIFF",),
    "zip": (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"),
}


def client_ip():
    return request.remote_addr or "unknown"


def login_key(username):
    return f"{client_ip()}:{username.casefold()}"


def csrf_token():
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


@app.context_processor
def inject_security_helpers():
    return {"csrf_token": csrf_token}


def csrf_protected(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        supplied = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token")
        expected = session.get("csrf_token")
        if not expected or not supplied or not secrets.compare_digest(supplied, expected):
            return jsonify({"error": "请求验证失败，请刷新页面后重试"}), 403
        return view(*args, **kwargs)

    return wrapped


def password_error(username, password):
    if len(password) < 8:
        return "密码长度至少为8位"
    if password.casefold() == username.casefold():
        return "密码不能与用户名相同"
    if password.casefold() in {item.casefold() for item in WEAK_PASSWORDS}:
        return "密码过于常见，请更换密码"
    if not any(char.isalpha() for char in password) or not any(char.isdigit() for char in password):
        return "密码至少包含字母和数字"
    return None


def record_login_failure(username, reason="invalid_credentials"):
    key = login_key(username)
    state = login_failures.setdefault(key, {"count": 0, "locked_until": 0})
    if state["locked_until"] and state["locked_until"] <= time.time():
        state["count"] = 0
        state["locked_until"] = 0
    state["count"] += 1
    if state["count"] >= LOGIN_MAX_FAILURES:
        state["locked_until"] = time.time() + LOGIN_LOCK_SECONDS
    security_logger.warning("login_failed username=%s ip=%s reason=%s count=%s", username, client_ip(), reason, state["count"])


def login_locked(username):
    state = login_failures.get(login_key(username))
    return bool(state and state["locked_until"] > time.time())


def clear_login_failures(username):
    login_failures.pop(login_key(username), None)


def get_db_connection():
    return pymysql.connect(**db_config)


def api_login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "username" not in session:
            return jsonify({"error": "请先登录"}), 401
        return view(*args, **kwargs)

    return wrapped


def current_user_files():
    username = session["username"]
    user_dir = os.path.join(app.config["UPLOAD_FOLDER"], username)
    os.makedirs(user_dir, exist_ok=True)
    files = []
    for filename in os.listdir(user_dir):
        path = os.path.join(user_dir, filename)
        if os.path.isfile(path):
            stat = os.stat(path)
            files.append(
                {
                    "name": filename,
                    "size": stat.st_size,
                    "updated_at": stat.st_mtime,
                }
            )
    return files


@app.get("/")
def index():
    return render_template("webpage.html")


@app.get("/login")
def login_page():
    csrf_token()
    return render_template("login.html")


@app.post("/login")
@csrf_protected
def login_post():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    result = _login(username, password, as_api=False)
    if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], int) and result[1] >= 400:
        return render_template("login.html", error=result[0], username=username), result[1]
    return result


def _login(username, password, as_api=True):
    if not username or not password:
        response = {"error": "请输入用户名和密码"}
        return (jsonify(response), 400) if as_api else ("请输入用户名和密码", 400)
    if login_locked(username):
        response = {"error": "用户名或密码错误"}
        return (jsonify(response), 401) if as_api else ("用户名或密码错误", 401)
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT username, password FROM users WHERE username=%s", (username,))
            user = cursor.fetchone()
    finally:
        conn.close()
    valid = bool(user) and (
        check_password_hash(user[1], password)
        if user and user[1].startswith(("pbkdf2:", "scrypt:"))
        else bool(user) and user[1] == password
    )
    if not valid:
        record_login_failure(username)
        response = {"error": "用户名或密码错误"}
        return (jsonify(response), 401) if as_api else ("用户名或密码错误", 401)
    clear_login_failures(username)
    session.clear()
    csrf_token()
    session["username"] = username
    if user and not user[1].startswith(("pbkdf2:", "scrypt:")):
        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE users SET password=%s WHERE username=%s", (generate_password_hash(password), username))
            conn.commit()
        finally:
            conn.close()
    security_logger.info("login_success username=%s ip=%s", username, client_ip())
    if as_api:
        return jsonify({"success": True, "user": {"username": username}})
    return redirect("/profile")


@app.post("/api/login")
@csrf_protected
def api_login():
    data = request.get_json(silent=True) or request.form
    return _login(data.get("username", "").strip(), data.get("password", ""))


@app.get("/api/me")
def api_me():
    if "username" not in session:
        return jsonify({"user": None}), 401
    return jsonify({"user": {"username": session["username"]}})


@app.get("/api/csrf")
def api_csrf():
    return jsonify({"csrf_token": csrf_token()})


@app.post("/api/logout")
@csrf_protected
def api_logout():
    session.clear()
    return jsonify({"success": True})


@app.get("/profile")
def profile():
    if "username" not in session:
        return redirect("/login")
    return render_template("profile.html")


@app.get("/logout")
def logout():
    session.clear()
    security_logger.info("logout ip=%s", client_ip())
    return redirect("/")


@app.get("/register")
def register_page():
    csrf_token()
    return render_template("register.html")


@app.post("/register")
@csrf_protected
def register_post():
    data = request.form
    result = _register(data.get("username", "").strip(), data.get("password", ""), data.get("confirm_password", ""))
    if result[1] != 200:
        payload = result[0].get_json(silent=True) if hasattr(result[0], "get_json") else {}
        return render_template("register.html", error=(payload or {}).get("error", "注册失败"), username=data.get("username", "")), result[1]
    return redirect("/")


def _register(username, password, confirm_password):
    if not username or not password:
        return jsonify({"error": "用户名和密码不能为空"}), 400
    if password != confirm_password:
        return jsonify({"error": "两次密码不一致"}), 400
    policy_error = password_error(username, password)
    if policy_error:
        return jsonify({"error": policy_error}), 400
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 FROM users WHERE username=%s", (username,))
            if cursor.fetchone():
                return jsonify({"error": "用户名已存在"}), 409
            cursor.execute(
                "INSERT INTO users(username, password) VALUES(%s, %s)",
                (username, generate_password_hash(password)),
            )
        conn.commit()
    finally:
        conn.close()
    return jsonify({"success": True}), 200


@app.post("/api/register")
@csrf_protected
def api_register():
    data = request.get_json(silent=True) or request.form
    return _register(data.get("username", "").strip(), data.get("password", ""), data.get("confirm_password", ""))


@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if "username" not in session:
        return redirect("/login")
    if request.method == "GET":
        return render_template("upload.html")
    supplied = request.form.get("csrf_token")
    if not supplied or not secrets.compare_digest(supplied, session.get("csrf_token", "")):
        return jsonify({"error": "请求验证失败，请刷新页面后重试"}), 403
    result = _save_upload(request.files.get("file"), request.form.get("customName", ""))
    return redirect("/listfiles") if result[1] == 200 else result


def _save_upload(file, custom_name=""):
    if not file or not file.filename:
        return jsonify({"error": "请选择文件"}), 400
    filename = secure_filename(custom_name.strip() or file.filename)
    if not filename:
        return jsonify({"error": "文件名无效"}), 400
    extension = filename.rsplit(".", 1)[-1].casefold() if "." in filename else ""
    if extension not in ALLOWED_EXTENSIONS:
        security_logger.warning("upload_rejected username=%s ip=%s filename=%s reason=extension", session.get("username"), client_ip(), filename)
        return jsonify({"error": "不支持的文件类型"}), 400
    if file.content_length and file.content_length > app.config["MAX_CONTENT_LENGTH"]:
        return jsonify({"error": "文件大小超过限制"}), 413
    signatures = FILE_SIGNATURES.get(extension)
    if signatures:
        header = file.stream.read(16)
        file.stream.seek(0)
        if not any(header.startswith(signature) for signature in signatures):
            security_logger.warning("upload_rejected username=%s ip=%s filename=%s reason=file_signature", session.get("username"), client_ip(), filename)
            return jsonify({"error": "文件内容与扩展名不匹配"}), 400
    user_dir = os.path.join(app.config["UPLOAD_FOLDER"], session["username"])
    os.makedirs(user_dir, exist_ok=True)
    file.save(os.path.join(user_dir, filename))
    security_logger.info("upload_success username=%s ip=%s filename=%s", session.get("username"), client_ip(), filename)
    return jsonify({"success": True, "file": filename}), 200


@app.post("/api/files")
@api_login_required
@csrf_protected
def api_upload_file():
    return _save_upload(request.files.get("file"), request.form.get("customName", ""))


@app.get("/listfiles")
def list_files():
    if "username" not in session:
        return redirect("/login")
    return render_template("filelist.html", username=session["username"], files=[item["name"] for item in current_user_files()])


@app.get("/api/files")
@api_login_required
def api_list_files():
    return jsonify({"files": current_user_files()})


def safe_user_file(filename):
    filename = secure_filename(filename or "")
    if not filename:
        abort(400, description="文件名无效")
    user_dir = os.path.join(app.config["UPLOAD_FOLDER"], session["username"])
    path = os.path.join(user_dir, filename)
    if not os.path.isfile(path):
        abort(404, description="文件不存在")
    return user_dir, filename


@app.get("/download")
def download_file():
    if "username" not in session:
        return "未登录", 401
    user_dir, filename = safe_user_file(request.args.get("filename"))
    return send_from_directory(user_dir, filename, as_attachment=True)


@app.get("/api/files/<path:filename>/download")
@api_login_required
def api_download_file(filename):
    user_dir, filename = safe_user_file(filename)
    return send_from_directory(user_dir, filename, as_attachment=True)


@app.route("/delete", methods=["GET", "DELETE"])
def delete_file():
    if "username" not in session:
        return "未登录", 401
    supplied = request.args.get("csrf_token") or request.headers.get("X-CSRF-Token")
    if not supplied or not secrets.compare_digest(supplied, session.get("csrf_token", "")):
        return jsonify({"error": "请求验证失败，请刷新页面后重试"}), 403
    user_dir, filename = safe_user_file(request.args.get("filename"))
    os.remove(os.path.join(user_dir, filename))
    return redirect("/listfiles") if request.method == "GET" else jsonify({"success": True})


@app.delete("/api/files/<path:filename>")
@api_login_required
@csrf_protected
def api_delete_file(filename):
    user_dir, filename = safe_user_file(filename)
    os.remove(os.path.join(user_dir, filename))
    return jsonify({"success": True})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5001")), debug=os.environ.get("FLASK_DEBUG", "0") == "1")

