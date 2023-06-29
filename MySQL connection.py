import mysql.connector
from mysql.connector import Error

# метод для подключения к базе
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


# подключение к базе
# connection = create_connection("127.0.0.1", "root", "wkiSyrOIh6)v", "Calendar")



# метод для работы с таблицами
def execute_query(connection, query):
	cursor = connection.cursor()
	try:
		cursor.execute(query)
		connection.commit()
		print("Запрос выполнен успешно")
	except Error as e:
		print(f"Произошла ошибка '{e}'")


# создание таблицы
# create_users_table = """
# CREATE TABLE IF NOT EXISTS Users (
# 	id INT AUTO_INCREMENT, 
# 	login VARCHAR(20) NOT NULL, 
# 	password VARCHAR(30) NOT NULL,
# 	PRIMARY KEY (id)
# ) ENGINE = InnoDB
# """
# execute_query(connection, create_users_table)


# создание связанной таблицы
# create_plans_table = """
# CREATE TABLE IF NOT EXISTS Plans (
# 	id INT AUTO_INCREMENT,
# 	idUser INT NOT NULL, 
# 	DependTime INT,
# 	DateEvent DATE,
# 	BeginTime DATETIME,
# 	EndTime DATETIME,
# 	Event VARCHAR(255),
# 	FOREIGN KEY plans (idUser) REFERENCES Users(id), 
# 	PRIMARY KEY (id)
# 	) ENGINE = InnoDB
# """
# execute_query(connection, create_plans_table)


# добавление записей
# create_Users = """
# INSERT INTO
# 	user (login, password)
# VALUES
# 	('mishael', '1234567890'),
# 	('kush', '0123456789');
# """
#execute_query(connection, create_Users)


# обновление записей
# update_plans_action = """
# UPDATE
# 	plans
# SET
# 	action = 'поесть'
# WHERE
# 	id = 2
# """
#execute_query(connection,  update_plans_action)


# удаление записей
# delete_plan = "DELETE FROM plans WHERE id = 2"
# execute_query(connection, delete_plan)



# метод для выбора записей
def execute_read_query(connection, query):
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except Error as e:
        print(f"Произошла ошибка '{e}'")


# выбор записей
# select_users = "SELECT * from users"
# users = execute_read_query(connection, select_users)
# for user in users:
#     print(user)
