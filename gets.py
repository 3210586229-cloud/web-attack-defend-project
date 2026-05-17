from flask import Flask, request,render_template,abort,send_file
from pathlib import Path
from typing import Optional
import pymysql
app=Flask(__name__)
##用于渲染profile页面（存在视频片段和jpg图片）
def first_existing_path(*candidates: str) -> Optional[Path]:
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return path
    return None


MEDIA_FILES = {
    "avatar": first_existing_path(
        r"C:\Users\byd\Pictures\化学有机\下载.webp",
        r"C:\Users\byd\Pictures\Camera Roll\laotou.jpg",
        r"C:\Users\byd\Pictures\Camera Roll\dayun.jpg",
    ),
    "video1": first_existing_path(
        r"C:\Users\byd\Videos\NVIDIA\League of Legends\League of Legends 2026.02.28 - 21.09.54.01.mp4",
    ),
    "video2": first_existing_path(
        r"C:\Users\byd\Videos\NVIDIA\Yuan Shen 原神\Yuan Shen 原神 2026.02.21 - 16.42.35.02.mp4",
    ),
}
##链接数据库
db_config={
    'host':'localhost',
    'user':'root',
    'password':'你的数据库密码',
    'database':'account_id',
    'charset':'utf8mb4'
}
def get_db_connection():
    return pymysql.connect(**db_config)

##创建页面使用@app.route
@app.route('/')
def index():
    return render_template('webpage.html')

@app.route('/login',methods=['GET'])
def login_page():
    return render_template('login.html')

@app.route('/login',methods=['POST'])
def login_post():
        #args只能用来提取url的参数
        #form可以读取页面输入文本的参数
        username_ = request.form.get('username')
        password_ = request.form.get('password')
        conn=get_db_connection()
        cursor=conn.cursor()
        sql=f"SELECT * FROM users WHERE username='{username_}'AND password='{password_}'"
        cursor.execute(sql)
        user=cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            return render_template('profile.html')
        else:
            return '<html><body><h2>登录失败</h2><a href="/login">回去重写</a></body></html>>'


        #return f"收到登录请求，用户名：{username_},密码：{password_}"
@app.route("/media/<name>")
def media(name: str):
    path = MEDIA_FILES.get(name)
    if path is None or not path.exists():
        abort(404)
    return send_file(path, conditional=True)

###注册功能实现
@app.route('/register',methods=['GET'])
def register_page():
    return render_template('register.html')

@app.route('/register',methods=['POST'])
def register_post():
    username_=request.form.get('username')
    password_=request.form.get('password')
    confirm_password_=request.form.get('confirm_password')
    if password_ !=confirm_password_:
        return '两次密码不一致'

    conn=get_db_connection()#建立连接
    cursor=conn.cursor()#获取游标
#sql拼接？
    sql=f"INSERT INTO users(username,password)VALUES('{username_}','{password_}')"
    try:
        cursor.execute(sql)
        conn.commit()

        return '<html><body><h2>注册成功</h2><a href="/login">去登陆</a></body></html>'
    except Exception as e:
        return f'<html><body><h2>注册失败</h2><p>{e}</p><a href="/register">返回</a></body></html>'
    finally:
        cursor.close()
        conn.close()


if __name__=='__main__':
    app.run(host='127.0.0.1',port=5001,debug=True)
