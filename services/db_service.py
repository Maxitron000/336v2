# services/db_service.py
import aiosqlite
from config import DB_NAME

class DBService:
    @staticmethod
    async def add_user(user_id, username, full_name):
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute(
                "INSERT OR REPLACE INTO users (id, username, full_name) VALUES (?, ?, ?)",
                (user_id, username, full_name)
            )
            await db.commit()

    @staticmethod
    async def get_user(user_id):
        async with aiosqlite.connect(DB_NAME) as db:
            async with db.execute("SELECT id, username, full_name, is_admin FROM users WHERE id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {"id": row[0], "username": row[1], "full_name": row[2], "is_admin": bool(row[3])}
                return None

    @staticmethod
    async def get_statistics():
        # Пример: вернуть количество пользователей
        async with aiosqlite.connect(DB_NAME) as db:
            async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                row = await cursor.fetchone()
                return {"users": row[0] if row else 0}

    @staticmethod
    async def add_record(user_id: int, action: str, location: str, comment: str = None):
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute(
                "INSERT INTO records (user_id, action, location, comment) VALUES (?, ?, ?, ?)",
                (user_id, action, location, comment)
            )
            await db.commit()

    @staticmethod
    async def get_user_records(user_id: int, limit: int = 10):
        async with aiosqlite.connect(DB_NAME) as db:
            async with db.execute(
                "SELECT id, action, location, timestamp, comment FROM records WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
                (user_id, limit)
            ) as cursor:
                return [
                    {"id": row[0], "action": row[1], "location": row[2], "timestamp": row[3], "comment": row[4]}
                    async for row in cursor
                ]

    @staticmethod
    async def get_all_records(days: int = 30):
        async with aiosqlite.connect(DB_NAME) as db:
            async with db.execute(
                "SELECT id, user_id, action, location, timestamp, comment FROM records WHERE timestamp >= datetime('now', ?) ORDER BY timestamp DESC",
                (f'-{days} days',)
            ) as cursor:
                return [
                    {"id": row[0], "user_id": row[1], "action": row[2], "location": row[3], "timestamp": row[4], "comment": row[5]}
                    async for row in cursor
                ]

    @staticmethod
    async def export_to_excel():
        # TODO: Реализовать экспорт в Excel асинхронно
        return "export.xlsx"