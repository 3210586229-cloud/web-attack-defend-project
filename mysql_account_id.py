import pymysql

db_config={
    'host':'localhost',
    'user':'root',
    'password':'pyk114514',
    'databse':'account_id',
    'charset':'utf-8'
}
def get_db_connection():
    return pymysql.connect(**db_config)

