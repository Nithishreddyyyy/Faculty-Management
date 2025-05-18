import mysql.connector
mycon = mysql.connector.connect(
    host="localhost",
    user="root",
    password="test1234")
mycur = mycon.cursor()
#mycur.execute("CREATE DATABASE IF NOT EXISTS iseTestDB")
for db in mycur:
    print(db)
