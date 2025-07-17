
import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd
import os

class DatabaseService:
    def __init__(self, db_name='military_tracker.db'):
        self.db_name = db_name
        self.init_database()

    def init_database(self):
        """Инициализация базы данных"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                
                # Таблица пользователей
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY,
                        username TEXT,
                        full_name TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Таблица записей
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        action TEXT NOT NULL,
                        location TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                ''')
                
                # Таблица админов
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS admins (
                        user_id INTEGER PRIMARY KEY,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                ''')
                
                conn.commit()
                print("✅ База данных инициализирована")
        except Exception as e:
            print(f"❌ Ошибка инициализации БД: {e}")

    def add_user(self, user_id: int, username: str, full_name: str) -> bool:
        """Добавление пользователя"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO users (id, username, full_name, last_activity)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''', (user_id, username, full_name))
                conn.commit()
                return True
        except Exception as e:
            print(f"Ошибка добавления пользователя: {e}")
            return False

    def get_user(self, user_id: int) -> Optional[Dict]:
        """Получение пользователя"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
                row = cursor.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'username': row[1], 
                        'full_name': row[2],
                        'created_at': row[3],
                        'last_activity': row[4]
                    }
                return None
        except Exception as e:
            print(f"Ошибка получения пользователя: {e}")
            return None

    def add_record(self, user_id: int, action: str, location: str) -> bool:
        """Добавление записи"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO records (user_id, action, location)
                    VALUES (?, ?, ?)
                ''', (user_id, action, location))
                
                # Обновляем последнюю активность пользователя
                cursor.execute('''
                    UPDATE users SET last_activity = CURRENT_TIMESTAMP WHERE id = ?
                ''', (user_id,))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Ошибка добавления записи: {e}")
            return False

    def get_user_records(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Получение записей пользователя"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT action, location, timestamp 
                    FROM records 
                    WHERE user_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (user_id, limit))
                
                rows = cursor.fetchall()
                return [
                    {
                        'action': row[0],
                        'location': row[1], 
                        'timestamp': row[2]
                    }
                    for row in rows
                ]
        except Exception as e:
            print(f"Ошибка получения записей: {e}")
            return []

    def is_admin(self, user_id: int) -> bool:
        """Проверка является ли пользователь админом"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT 1 FROM admins WHERE user_id = ?', (user_id,))
                return cursor.fetchone() is not None
        except Exception as e:
            print(f"Ошибка проверки админа: {e}")
            return False

    def add_admin(self, user_id: int) -> bool:
        """Добавление админа"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO admins (user_id) VALUES (?)
                ''', (user_id,))
                conn.commit()
                return True
        except Exception as e:
            print(f"Ошибка добавления админа: {e}")
            return False

    def get_current_status(self):
        """Получить текущий статус для веб-интерфейса"""
        try:
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

    def execute_query(self, query: str, params=None):
        """Выполнение SQL запроса"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                return cursor.fetchall()
        except Exception as e:
            print(f"Ошибка выполнения запроса: {e}")
            return []
