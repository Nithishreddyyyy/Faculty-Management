import mysql.connector
mycon = mysql.connector.connect(
    host="localhost",
    user="root",
    password="test@1234")
mycur = mycon.cursor()
# mycur.execute("CREATE DATABASE IF NOT EXISTS iseTestDB")
# mycur.execute("SHOW DATABASES")
for db in mycur:
    print(db)
