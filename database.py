import sqlite3
import pandas as pd
import openpyxl
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from config import DB_NAME, MAIN_ADMIN_ID, EXPORT_FILENAME

class Database:
    def __init__(self):
        self.db_name = DB_NAME
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                full_name TEXT NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                comment TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Таблица админов с правами
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                permissions TEXT,
                appointed_by INTEGER,
                appointed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (appointed_by) REFERENCES users (id)
            )
        ''')
        
        # Добавляем главного админа если его нет
        if MAIN_ADMIN_ID:
            cursor.execute('''
                INSERT OR IGNORE INTO users (id, username, full_name, is_admin)
                VALUES (?, ?, ?, ?)
            ''', (MAIN_ADMIN_ID, 'main_admin', 'Главный администратор', True))
            
            cursor.execute('''
                INSERT OR IGNORE INTO admins (id, username, permissions, appointed_by)
                VALUES (?, ?, ?, ?)
            ''', (MAIN_ADMIN_ID, 'main_admin', 'all', MAIN_ADMIN_ID))
        
        conn.commit()
        conn.close()
    
    def add_user(self, user_id: int, username: str, full_name: str) -> bool:
        """Добавление нового пользователя"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO users (id, username, full_name)
                VALUES (?, ?, ?)
            ''', (user_id, username, full_name))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка добавления пользователя: {e}")
            return False
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Получение информации о пользователе"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, full_name, is_admin FROM users WHERE id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'username': result[1],
                'full_name': result[2],
                'is_admin': bool(result[3])
            }
        return None
    
    def is_admin(self, user_id: int) -> bool:
        """Проверка является ли пользователь админом"""
        user = self.get_user(user_id)
        return user['is_admin'] if user else False
    
    def is_main_admin(self, user_id: int) -> bool:
        """Проверка является ли пользователь главным админом"""
        return user_id == MAIN_ADMIN_ID
    
    def add_record(self, user_id: int, action: str, location: str, comment: str = None) -> bool:
        """Добавление записи о выходе/приходе"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO records (user_id, action, location, comment)
                VALUES (?, ?, ?, ?)
            ''', (user_id, action, location, comment))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка добавления записи: {e}")
            return False
    
    def get_user_records(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Получение записей пользователя"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, action, location, timestamp, comment
            FROM records 
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (user_id, limit))
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'action': row[1],
                'location': row[2],
                'timestamp': row[3],
                'comment': row[4]
            }
            for row in results
        ]
    
    def get_all_records(self, days: int = 30) -> List[Dict]:
        """Получение всех записей за период"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT r.id, u.full_name, r.action, r.location, r.timestamp, r.comment
            FROM records r
            JOIN users u ON r.user_id = u.id
            WHERE r.timestamp >= datetime('now', '-{} days')
            ORDER BY r.timestamp DESC
        '''.format(days))
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'full_name': row[1],
                'action': row[2],
                'location': row[3],
                'timestamp': row[4],
                'comment': row[5]
            }
            for row in results
        ]
    
    def get_statistics(self, days: int = 30) -> Dict:
        """Получение статистики"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Общая статистика
        cursor.execute('''
            SELECT COUNT(*) FROM records 
            WHERE timestamp >= datetime('now', '-{} days')
        '''.format(days))
        total_records = cursor.fetchone()[0]
        
        # Статистика по действиям
        cursor.execute('''
            SELECT action, COUNT(*) FROM records 
            WHERE timestamp >= datetime('now', '-{} days')
            GROUP BY action
        '''.format(days))
        action_stats = dict(cursor.fetchall())
        
        # Статистика по локациям
        cursor.execute('''
            SELECT location, COUNT(*) FROM records 
            WHERE timestamp >= datetime('now', '-{} days')
            GROUP BY location
            ORDER BY COUNT(*) DESC
        '''.format(days))
        location_stats = dict(cursor.fetchall())
        
        # Активные пользователи
        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) FROM records 
            WHERE timestamp >= datetime('now', '-{} days')
        '''.format(days))
        active_users = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_records': total_records,
            'action_stats': action_stats,
            'location_stats': location_stats,
            'active_users': active_users
        }
    
    def export_to_excel(self, days: int = 30) -> str:
        """Экспорт данных в Excel"""
        records = self.get_all_records(days)
        
        if not records:
            return None
        
        df = pd.DataFrame(records)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp', ascending=False)
        
        # Создаем Excel файл с цветовой схемой
        with pd.ExcelWriter(EXPORT_FILENAME, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Записи', index=False)
            
            # Получаем рабочую книгу для форматирования
            workbook = writer.book
            worksheet = writer.sheets['Записи']
            
            # Применяем цветовую схему
            for row in range(2, len(df) + 2):  # Начинаем с 2 (после заголовков)
                action = worksheet.cell(row=row, column=3).value  # Колонка action
                if action == 'убыл':
                    worksheet.cell(row=row, column=3).fill = openpyxl.styles.PatternFill(
                        start_color='FF0000', end_color='FF0000', fill_type='solid'
                    )
                elif action == 'прибыл':
                    worksheet.cell(row=row, column=3).fill = openpyxl.styles.PatternFill(
                        start_color='00FF00', end_color='00FF00', fill_type='solid'
                    )
        
        return EXPORT_FILENAME
    
    def cleanup_old_records(self, months: int = 6):
        """Очистка старых записей (старше 6 месяцев)"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM records 
            WHERE timestamp < datetime('now', '-{} months')
        '''.format(months))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted_count
    
    def get_all_admins(self) -> List[Dict]:
        """Получение списка всех администраторов"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.id, u.username, u.full_name, a.permissions
            FROM users u
            JOIN admins a ON u.id = a.id
            WHERE u.is_admin = TRUE
            ORDER BY u.full_name
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'username': row[1],
                'full_name': row[2],
                'permissions': row[3]
            }
            for row in results
        ]
    
    def add_admin(self, user_id: int, permissions: str = "basic") -> bool:
        """Добавление нового администратора"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            # Обновляем статус пользователя
            cursor.execute('''
                UPDATE users SET is_admin = TRUE WHERE id = ?
            ''', (user_id,))
            
            # Добавляем в таблицу админов
            user = self.get_user(user_id)
            if user:
                cursor.execute('''
                    INSERT OR REPLACE INTO admins (id, username, permissions, appointed_by)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, user['username'], permissions, MAIN_ADMIN_ID))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка добавления админа: {e}")
            return False
    
    def remove_admin(self, user_id: int) -> bool:
        """Удаление администратора"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            # Нельзя удалить главного админа
            if user_id == MAIN_ADMIN_ID:
                return False
            
            # Обновляем статус пользователя
            cursor.execute('''
                UPDATE users SET is_admin = FALSE WHERE id = ?
            ''', (user_id,))
            
            # Удаляем из таблицы админов
            cursor.execute('''
                DELETE FROM admins WHERE id = ?
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка удаления админа: {e}")
            return False
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Получение пользователя по ID"""
        return self.get_user(user_id)