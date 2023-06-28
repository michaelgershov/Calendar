import mysql.connector
from mysql.connector import Error

def create_connection(host_name, user_name, user_password, db_name):
	connection = None
	try:
		connection = mysql.connector.connect(
			host=host_name,
            		user=user_name,
			passwd=user_password,
			database=db_name
		)
		print("Подключение к базе данных MySQL прошло успешно")
	except Error as e:
		print(f"Произошла ошибка '{e}'")
	return connection
connection = create_connection("127.0.0.1", "root", "1234", "calendar")
