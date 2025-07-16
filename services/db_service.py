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
    async def export_to_excel():
        # Заглушка: возвращает путь к файлу
        return "export.xlsx"