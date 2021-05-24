import mysql.connector

mydb = mysql.connector.connect(
  host="MacBook-Pro-van-Imre.local",
  user="root",
  password="root"
)


mycursor = mydb.cursor()
mycursor.execute("SELECT * FROM kbs.temp")
myresult = mycursor.fetchall()

for x in myresult:
  print(x)