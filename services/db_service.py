import sqlite3

class DatabaseService:
    def __init__(self, db_name='mydatabase.db'):
        self.db_name = db_name
        self.conn = None
        self.cursor = None

    def connect(self):
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")
            self.conn = None
            self.cursor = None
            raise

    def disconnect(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def execute_query(self, query, params=()):
        try:
            self.connect()
            self.cursor.execute(query, params)
            self.conn.commit()
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Query execution error: {e}")
            return None
        finally:
            self.disconnect()

    def create_table(self, table_name, columns):
        column_defs = ', '.join(columns)
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({column_defs})"
        self.execute_query(query)

    def insert_data(self, table_name, data):
        placeholders = ', '.join(['?'] * len(data))
        columns = ', '.join(data.keys())
        values = tuple(data.values())
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        self.execute_query(query, values)

    def fetch_data(self, table_name, condition=None):
        query = f"SELECT * FROM {table_name}"
        if condition:
            query += f" WHERE {condition}"
        return self.execute_query(query)

    def get_current_status(self):
        """Получить текущий статус для веб-интерфейса"""
        try:
            # Заглушка для демонстрации
            return {
                'total': 10,
                'present': 7,
                'absent': 3,
                'unknown': 0,
                'present_list': [
                    {'name': 'Иванов И.И.', 'last_update': '2025-01-17T10:30:00'},
                    {'name': 'Петров П.П.', 'last_update': '2025-01-17T09:15:00'},
                ],
                'absent_list': [
                    {'name': 'Сидоров С.С.', 'location': 'Отпуск', 'last_update': '2025-01-16T18:00:00'},
                    {'name': 'Козлов К.К.', 'location': 'Командировка', 'last_update': '2025-01-16T16:30:00'},
                ]
            }
        except Exception as e:
            print(f"Ошибка получения статуса: {e}")
            return {
                'total': 0,
                'present': 0,
                'absent': 0,
                'unknown': 0,
                'present_list': [],
                'absent_list': []
            }

# Example usage (can be removed or commented out for production)
if __name__ == '__main__':
    db_service = DatabaseService()

    # Create a table
    db_service.create_table(
        'users',
        ['id INTEGER PRIMARY KEY', 'name TEXT', 'email TEXT']
    )

    # Insert data
    db_service.insert_data(
        'users',
        {'name': 'John Doe', 'email': 'john.doe@example.com'}
    )
    db_service.insert_data(
        'users',
        {'name': 'Jane Smith', 'email': 'jane.smith@example.com'}
    )

    # Fetch and print data
    users = db_service.fetch_data('users')
    if users:
        for user in users:
            print(user)