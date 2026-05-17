from flask import Flask, request,render_template,redirect,abort,send_from_directory,session
import os
from werkzeug.utils import secure_filename
import pymysql
from flask import session
app=Flask(__name__)
app.secret_key='my-secret-key'##session加密码


db_config={
    'host':'localhost',
    'user':'root',
    'password':'pyk114514',
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
        conn=get_db_connection()#建立连接
        cursor=conn.cursor()#获取游标
        sql=f"SELECT * FROM users WHERE username='{username_}'AND password='{password_}'"
        cursor.execute(sql)
        user=cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            session['username']=username_##记录登录状态
            return redirect('/profile')
        else:
            return '<html><body><h2>登录失败</h2><a href="/login">回去重写</a></body></html>>'
##判断登录状态
@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect('/login')
    return render_template('profile.html')##原视频为返回文件列表

@app.route('/logout')##登出表单
def logout():
    session.clear()
    return redirect('/')


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
    cursor.execute("SELECT * FROM users WHERE username=%s", (username_,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return render_template('register.html', username=username_, username_error='用户名已存在')
#sql拼接？
    sql=f"INSERT INTO users(username,password)VALUES('{username_}','{password_}')"
    try:
        cursor.execute(sql)
        conn.commit()

        return redirect('/')
    except Exception as e:
        return f'<html><body><h2>注册失败</h2><p>{e}</p><a href="/register">返回</a></body></html>'
    finally:
        cursor.close()
        conn.close()


##上传文件
UPLOAD_FOLDER = 'uploads'  # 相对路径，会在根目录下创建
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER  ##什么玩意儿？
@app.route('/upload',methods=['GET','POST'])
def upload_file():
    if 'username' not in session:
        return redirect('/login')##稍作改变返回登陆界面
    if request.method=='GET':
        return render_template('upload.html')
    username_=session['username']

    ##获取上传的文件对象
    file=request.files['file']
    if file.filename=='':
        return "未选择文件"

    ##获取用户自定义文件名
    custom_name=request.form.get('customName','')
    if custom_name.strip():
        filename=secure_filename(custom_name)##防止路径遍历攻击？
    else:
        filename=secure_filename(file.filename)

    ##创建用户目录
    user_dir=os.path.join(app.config['UPLOAD_FOLDER'],username_)
    os.makedirs(user_dir,exist_ok=True)

    ##保存文件
    save_path=os.path.join(user_dir,filename)
    file.save(save_path)

    return redirect('/listfiles')

##展示文件列表并提供下载链接
@app.route('/listfiles')
def list_files():
    if 'username' not in session:
        return redirect('/login')
    username_ = session['username']
    user_dir=os.path.join(app.config['UPLOAD_FOLDER'],username_)

    files=[]
    if os.path.exists(user_dir):
        for filename in os.listdir(user_dir):
            filepath=os.path.join(user_dir,filename)
            if os.path.isfile(filepath):
                files.append(filename)
    return render_template('filelist.html',username=username_,files=files)
### 文件下载功能（新增）
@app.route('/download')
def download_file():
    if 'username' not in session:
        return "未登录", 401
    username_ = session['username']
    filename = request.args.get('filename')
    if not filename:
        return "缺少文件名", 400
    user_dir = os.path.join(app.config['UPLOAD_FOLDER'], username_)
    file_path = os.path.join(user_dir, filename)
    if not os.path.exists(file_path):
        abort(404)
        ##最后一步发送文件
    return send_from_directory(user_dir, filename, as_attachment=True)


### 文件删除功能（新增）
@app.route('/delete')
def delete_file():
    if 'username' not in session:
        return "未登录", 401
    username_ = session['username']
    filename = request.args.get('filename')
    if not filename:
        return "缺少文件名", 400
    user_dir = os.path.join(app.config['UPLOAD_FOLDER'], username_)
    file_path = os.path.join(user_dir, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return redirect('/listfiles')
    else:
        return "文件不存在", 404


if __name__=='__main__':
    app.run(host='127.0.0.1',port=5001,debug=True)
