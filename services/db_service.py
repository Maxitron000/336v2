import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import pandas as pd
import os

class DatabaseService:
    def __init__(self, db_path: str = "military_tracker.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Инициализация базы данных"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY,
                        username TEXT NOT NULL,
                        full_name TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_admin BOOLEAN DEFAULT FALSE
                    )
                ''')

                conn.execute('''
                    CREATE TABLE IF NOT EXISTS records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        action TEXT NOT NULL,
                        location TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                ''')

                conn.execute('''
                    CREATE TABLE IF NOT EXISTS admins (
                        user_id INTEGER PRIMARY KEY,
                        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                ''')

                # Создаем индексы для улучшения производительности
                conn.execute('CREATE INDEX IF NOT EXISTS idx_records_user_id ON records (user_id)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_records_timestamp ON records (timestamp)')

                conn.commit()
                logging.info("✅ База данных инициализирована")
        except Exception as e:
            logging.error(f"Ошибка инициализации БД: {e}")

    def add_user(self, user_id: int, username: str, full_name: str) -> bool:
        """Добавить пользователя"""
        try:
            # Валидация входных данных
            if not isinstance(user_id, int) or user_id <= 0:
                logging.error(f"Некорректный user_id: {user_id}")
                return False
            
            if not username or len(username.strip()) == 0:
                logging.error("Пустое имя пользователя")
                return False
            
            if not full_name or len(full_name.strip()) < 3 or len(full_name.strip()) > 50:
                logging.error(f"Некорректное ФИО: {full_name}")
                return False
            
            username = username.strip()[:50]  # Ограничиваем длину
            full_name = full_name.strip()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    'INSERT OR REPLACE INTO users (id, username, full_name) VALUES (?, ?, ?)',
                    (user_id, username, full_name)
                )
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Ошибка добавления пользователя: {e}")
            return False

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    'SELECT * FROM users WHERE id = ?',
                    (user_id,)
                )
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logging.error(f"Ошибка получения пользователя: {e}")
            return None

    def add_record(self, user_id: int, action: str, location: str) -> bool:
        """Добавить запись"""
        try:
            # Валидация входных данных
            if not isinstance(user_id, int) or user_id <= 0:
                logging.error(f"Некорректный user_id: {user_id}")
                return False
            
            if not action or action.strip() not in ['в части', 'не в части', 'прибыл', 'убыл']:
                logging.error(f"Некорректное действие: {action}")
                return False
            
            if not location or len(location.strip()) < 1 or len(location.strip()) > 100:
                logging.error(f"Некорректная локация: {location}")
                return False
            
            # Проверяем, существует ли пользователь
            if not self.get_user(user_id):
                logging.error(f"Пользователь {user_id} не найден")
                return False
            
            action = action.strip()
            location = location.strip()
            
            # Проверяем последнее действие пользователя (защита от дублирования)
            last_records = self.get_user_records(user_id, 1)
            if last_records:
                last_action = last_records[0]['action']
                if last_action == action:
                    logging.warning(f"Попытка дублирования действия '{action}' пользователем {user_id}")
                    return False
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    'INSERT INTO records (user_id, action, location) VALUES (?, ?, ?)',
                    (user_id, action, location)
                )
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Ошибка добавления записи: {e}")
            return False

    def get_user_records(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Получить записи пользователя"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    'SELECT * FROM records WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?',
                    (user_id, limit)
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Ошибка получения записей пользователя: {e}")
            return []

    def get_all_records(self, days: int = 7, limit: int = 100) -> List[Dict[str, Any]]:
        """Получить все записи за период"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                since_date = datetime.now() - timedelta(days=days)
                cursor = conn.execute('''
                    SELECT r.*, u.full_name 
                    FROM records r
                    JOIN users u ON r.user_id = u.id
                    WHERE r.timestamp > ?
                    ORDER BY r.timestamp DESC
                    LIMIT ?
                ''', (since_date, limit))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Ошибка получения всех записей: {e}")
            return []

    def get_current_status(self) -> Dict[str, Any]:
        """Получить текущий статус всех пользователей"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                # Получаем всех пользователей
                users_cursor = conn.execute('SELECT id, full_name FROM users')
                all_users = users_cursor.fetchall()

                # Получаем последние действия каждого пользователя
                absent_list = []
                present_count = 0

                for user in all_users:
                    last_record_cursor = conn.execute('''
                        SELECT action, location FROM records 
                        WHERE user_id = ? 
                        ORDER BY timestamp DESC 
                        LIMIT 1
                    ''', (user['id'],))
                    last_record = last_record_cursor.fetchone()

                    if last_record and last_record['action'] == 'убыл':
                        absent_list.append({
                            'name': user['full_name'],
                            'location': last_record['location']
                        })
                    else:
                        present_count += 1

                return {
                    'total': len(all_users),
                    'present': present_count,
                    'absent': len(absent_list),
                    'absent_list': absent_list
                }
        except Exception as e:
            logging.error(f"Ошибка получения статуса: {e}")
            return {'total': 0, 'present': 0, 'absent': 0, 'absent_list': []}

    def is_admin(self, user_id: int) -> bool:
        """Проверить права администратора"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    'SELECT 1 FROM admins WHERE user_id = ?',
                    (user_id,)
                )
                return cursor.fetchone() is not None
        except Exception as e:
            logging.error(f"Ошибка проверки прав админа: {e}")
            return False

    def add_admin(self, user_id: int) -> bool:
        """Добавить администратора"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    'INSERT OR IGNORE INTO admins (user_id) VALUES (?)',
                    (user_id,)
                )
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Ошибка добавления админа: {e}")
            return False

    def get_all_admins(self) -> List[Dict[str, Any]]:
        """Получить всех админов"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT u.id, u.username, u.full_name, a.added_at
                    FROM admins a
                    JOIN users u ON a.user_id = u.id
                    ORDER BY a.added_at
                ''')
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Ошибка получения админов: {e}")
            return []

    def get_all_users(self) -> List[Dict[str, Any]]:
        """Получить всех пользователей"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('SELECT * FROM users ORDER BY full_name')
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Ошибка получения пользователей: {e}")
            return []

    def export_to_excel(self, days: int = 30) -> Optional[str]:
        """Экспорт данных в Excel"""
        try:
            records = self.get_all_records(days=days, limit=10000)

            if not records:
                return None

            # Создаем DataFrame
            df = pd.DataFrame(records)

            # Форматируем данные
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp', ascending=False)

            # Переименовываем колонки
            df = df.rename(columns={
                'full_name': 'ФИО',
                'action': 'Действие',
                'location': 'Локация',
                'timestamp': 'Дата_Время'
            })

            # Убираем эмодзи из локаций
            df['Локация'] = df['Локация'].str.replace(r'[^\w\s\-\.\,\(\)]', '', regex=True).str.strip()

            # Создаем отдельные столбцы для даты и времени
            df['Дата'] = df['Дата_Время'].dt.strftime('%d.%m.%Y')
            df['Время'] = df['Дата_Время'].dt.strftime('%H:%M:%S')

            # Выбираем нужные колонки в правильном порядке
            df = df[['ФИО', 'Действие', 'Локация', 'Дата', 'Время']]

            # Сохраняем в файл
            filename = f"military_records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

            # Создаем Excel файл с улучшенным форматированием
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Записи', index=False)

                # Получаем рабочий лист и стили
                worksheet = writer.sheets['Записи']
                from openpyxl.styles import PatternFill, Font, Alignment, Border, Side

                # Определяем стили
                header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
                header_font = Font(color="FFFFFF", bold=True, size=12)

                arrived_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")  # Светло-зеленый
                departed_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")  # Светло-красный

                border = Border(
                    left=Side(style='thin'),
                    right=Side(style='thin'),
                    top=Side(style='thin'),
                    bottom=Side(style='thin')
                )

                # Форматируем заголовки
                for cell in worksheet[1]:
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = Alignment(horizontal='center', vertical='center')
                    cell.border = border

                # Форматируем данные с цветовой заливкой
                for row_num, row in enumerate(worksheet.iter_rows(min_row=2), start=2):
                    action_cell = row[1]  # Колонка "Действие"

                    for cell in row:
                        cell.border = border
                        cell.alignment = Alignment(horizontal='left', vertical='center')

                        # Применяем цветовую заливку в зависимости от действия
                        if action_cell.value == "прибыл":
                            cell.fill = arrived_fill
                        elif action_cell.value == "убыл":
                            cell.fill = departed_fill

                # Автоматически подгоняем ширину колонок
                column_widths = {
                    'A': 0,  # ФИО
                    'B': 0,  # Действие  
                    'C': 0,  # Локация
                    'D': 0,  # Дата
                    'E': 0   # Время
                }
                
                # Определяем максимальную ширину для каждой колонки
                for row in worksheet.iter_rows():
                    for cell in row:
                        column_letter = cell.column_letter
                        if column_letter in column_widths:
                            try:
                                cell_length = len(str(cell.value)) if cell.value else 0
                                if cell_length > column_widths[column_letter]:
                                    column_widths[column_letter] = cell_length
                            except:
                                pass
                
                # Устанавливаем ширину колонок с особыми настройками
                worksheet.column_dimensions['A'].width = max(column_widths['A'] + 3, 20)  # ФИО - минимум 20
                worksheet.column_dimensions['B'].width = max(column_widths['B'] + 2, 12)  # Действие - минимум 12
                worksheet.column_dimensions['C'].width = max(column_widths['C'] + 2, 15)  # Локация - минимум 15
                worksheet.column_dimensions['D'].width = 12  # Дата - фиксированная ширина
                worksheet.column_dimensions['E'].width = 10  # Время - фиксированная ширина

                # Устанавливаем высоту строк
                for row in worksheet.iter_rows():
                    worksheet.row_dimensions[row[0].row].height = 20

            return filename
        except Exception as e:
            logging.error(f"Ошибка экспорта в Excel: {e}")
            return None

    def get_records_by_date(self, date_str: str) -> List[Dict[str, Any]]:
        """Получить записи за конкретную дату"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT r.*, u.full_name 
                    FROM records r
                    JOIN users u ON r.user_id = u.id
                    WHERE DATE(r.timestamp) = ?
                    ORDER BY r.timestamp DESC
                ''', (date_str,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Ошибка получения записей по дате: {e}")
            return []

    def cleanup_old_records(self, days: int = 180) -> int:
        """Очистка старых записей"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cutoff_date = datetime.now() - timedelta(days=days)
                cursor = conn.execute(
                    'DELETE FROM records WHERE timestamp < ?',
                    (cutoff_date,)
                )
                deleted_count = cursor.rowcount
                conn.commit()
                return deleted_count
        except Exception as e:
            logging.error(f"Ошибка очистки записей: {e}")
            return 0