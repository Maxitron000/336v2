import aiosqlite
from config import DB_NAME
import logging

class DBService:
    @staticmethod
    async def add_user(user_id, username, full_name):
        """Добавление пользователя"""
        try:
            async with aiosqlite.connect(DB_NAME) as db:
                await db.execute(
                    "INSERT OR REPLACE INTO users (id, username, full_name) VALUES (?, ?, ?)",
                    (user_id, username, full_name)
                )
                await db.commit()
                return True
        except Exception as e:
            logging.error(f"Ошибка добавления пользователя: {e}")
            return False

    @staticmethod
    async def get_user(user_id):
        """Получение пользователя"""
        try:
            async with aiosqlite.connect(DB_NAME) as db:
                async with db.execute("SELECT id, username, full_name, is_admin FROM users WHERE id = ?", (user_id,)) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        return {"id": row[0], "username": row[1], "full_name": row[2], "is_admin": bool(row[3])}
                    return None
        except Exception as e:
            logging.error(f"Ошибка получения пользователя: {e}")
            return None

    @staticmethod
    async def get_statistics():
        """Получение статистики"""
        try:
            async with aiosqlite.connect(DB_NAME) as db:
                async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                    users_count = (await cursor.fetchone())[0]

                async with db.execute("SELECT COUNT(*) FROM records") as cursor:
                    records_count = (await cursor.fetchone())[0]

                return {
                    'users': users_count,
                    'records': records_count
                }
        except Exception as e:
            logging.error(f"Ошибка получения статистики: {e}")
            return {'users': 0, 'records': 0}

    @staticmethod
    async def add_record(user_id: int, action: str, location: str, comment: str = None):
        """Добавление записи"""
        try:
            async with aiosqlite.connect(DB_NAME) as db:
                await db.execute(
                    "INSERT INTO records (user_id, action, location, comment) VALUES (?, ?, ?, ?)",
                    (user_id, action, location, comment)
                )
                await db.commit()
                return True
        except Exception as e:
            logging.error(f"Ошибка добавления записи: {e}")
            return False

    @staticmethod
    async def get_user_records(user_id: int, limit: int = 10):
        """Получение записей пользователя"""
        try:
            async with aiosqlite.connect(DB_NAME) as db:
                async with db.execute(
                    "SELECT id, action, location, timestamp, comment FROM records WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
                    (user_id, limit)
                ) as cursor:
                    records = []
                    async for row in cursor:
                        records.append({
                            "id": row[0], 
                            "action": row[1], 
                            "location": row[2], 
                            "timestamp": row[3], 
                            "comment": row[4]
                        })
                    return records
        except Exception as e:
            logging.error(f"Ошибка получения записей пользователя: {e}")
            return []

    @staticmethod
    async def get_all_records(days: int = 30):
        """Получение всех записей"""
        try:
            async with aiosqlite.connect(DB_NAME) as db:
                async with db.execute(
                    "SELECT id, user_id, action, location, timestamp, comment FROM records WHERE timestamp >= datetime('now', ?) ORDER BY timestamp DESC",
                    (f'-{days} days',)
                ) as cursor:
                    records = []
                    async for row in cursor:
                        records.append({
                            "id": row[0], 
                            "user_id": row[1], 
                            "action": row[2], 
                            "location": row[3], 
                            "timestamp": row[4], 
                            "comment": row[5]
                        })
                    return records
        except Exception as e:
            logging.error(f"Ошибка получения всех записей: {e}")
            return []

    @staticmethod
    async def export_to_excel():
        """Экспорт в Excel"""
        # TODO: Реализовать экспорт в Excel асинхронно
        return "export.xlsx"

    @staticmethod
    async def get_all_users():
        """Получить всех пользователей"""
        try:
            async with aiosqlite.connect(DB_NAME) as db:
                async with db.execute("""
                    SELECT id, username, full_name, is_admin, created_at
                    FROM users
                    ORDER BY created_at DESC
                """) as cursor:
                    rows = await cursor.fetchall()

                users = []
                for row in rows:
                    users.append({
                        'id': row[0],
                        'username': row[1],
                        'full_name': row[2],
                        'is_admin': bool(row[3]),
                        'created_at': row[4]
                    })

                return users
        except Exception as e:
            logging.error(f"Ошибка получения пользователей: {e}")
            return []

    @staticmethod
    async def get_all_records_with_names(limit=50):
        """Получить все записи"""
        try:
            async with aiosqlite.connect(DB_NAME) as db:
                async with db.execute("""
                    SELECT r.id, r.user_id, r.action, r.location, r.timestamp,
                           u.full_name
                    FROM records r
                    JOIN users u ON r.user_id = u.id
                    ORDER BY r.timestamp DESC
                    LIMIT ?
                """, (limit,)) as cursor:
                    rows = await cursor.fetchall()

                records = []
                for row in rows:
                    records.append({
                        'id': row[0],
                        'user_id': row[1],
                        'action': row[2],
                        'location': row[3],
                        'timestamp': row[4],
                        'full_name': row[5]
                    })

                return records
        except Exception as e:
            logging.error(f"Ошибка получения записей: {e}")
            return []

    @staticmethod
    async def get_records_by_date(date):
        """Получить записи по дате"""
        try:
            async with aiosqlite.connect(DB_NAME) as db:
                cursor = await db.execute(
                    """
                    SELECT id, user_id, action, location, timestamp, comment
                    FROM records
                    WHERE DATE(timestamp) = ?
                    ORDER BY timestamp DESC
                    """,
                    (date,)
                )
                records = await cursor.fetchall()

                return [
                    {
                        'id': record[0],
                        'user_id': record[1],
                        'action': record[2],
                        'location': record[3],
                        'timestamp': record[4],
                        'comment': record[5]
                    }
                    for record in records
                ]
        except Exception as e:
            logging.error(f"Ошибка получения записей по дате: {e}")
            return []