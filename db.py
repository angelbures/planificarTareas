import pymysql

def get_connection():
    return pymysql.connect(
        host="localhost",
        user="root",         # ⚠️ pon tu usuario
        password="RootSQL", # ⚠️ pon tu password
        database="planner",
        cursorclass=pymysql.cursors.DictCursor
    )