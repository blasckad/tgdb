from arango import ArangoClient

# Конфигурация подключения к базе данных
DB_NAME = "TemporalGraphDB"
USERNAME = "root"
PASSWORD = "my_password"

def get_database():
    client = ArangoClient()
    sys_db = client.db('_system', username=USERNAME, password=PASSWORD)

    # Создание базы данных, если она не существует
    if not sys_db.has_database(DB_NAME):
        sys_db.create_database(DB_NAME)

    return client.db(DB_NAME, username=USERNAME, password=PASSWORD)
