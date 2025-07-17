
import logging
import asyncio
from datetime import datetime, timedelta
from services.db_service import DatabaseService

class SystemMonitor:
    def __init__(self):
        self.db = DatabaseService()
        self.logger = logging.getLogger(__name__)
    
    async def check_system_health(self):
        """Проверка состояния системы"""
        health_report = {
            'timestamp': datetime.now().isoformat(),
            'database': await self._check_database(),
            'users': await self._check_users(),
            'records': await self._check_records(),
            'system': await self._check_system()
        }
        return health_report
    
    async def _check_database(self):
        """Проверка состояния БД"""
        try:
            users = self.db.get_all_users()
            records = self.db.get_all_records(days=1, limit=1)
            
            return {
                'status': 'healthy',
                'total_users': len(users) if users else 0,
                'recent_activity': len(records) > 0
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def _check_users(self):
        """Проверка пользователей"""
        try:
            stats = self.db.get_current_status()
            return {
                'total': stats.get('total', 0),
                'present': stats.get('present', 0),
                'absent': stats.get('absent', 0),
                'absent_locations': [user['location'] for user in stats.get('absent_list', [])]
            }
        except Exception as e:
            self.logger.error(f"Ошибка проверки пользователей: {e}")
            return {'error': str(e)}
    
    async def _check_records(self):
        """Проверка записей"""
        try:
            # Получаем записи за последние 24 часа
            yesterday = datetime.now() - timedelta(days=1)
            records_today = self.db.get_all_records(days=1, limit=1000)
            
            return {
                'status': 'checked',
                'records_today': len(records_today),
                'last_activity': records_today[0]['timestamp'] if records_today else None
            }
        except Exception as e:
            return {'error': str(e)}
    
    async def _check_system(self):
        """Проверка системы"""
        try:
            import psutil
            import os
            
            # Проверяем использование ресурсов
            memory_percent = psutil.virtual_memory().percent
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Проверяем размер БД
            db_size = os.path.getsize('military_tracker.db') if os.path.exists('military_tracker.db') else 0
            
            return {
                'memory_usage': memory_percent,
                'cpu_usage': cpu_percent,
                'db_size_mb': db_size / (1024 * 1024)
            }
        except Exception as e:
            return {'error': str(e)}
    
    async def analyze_user_patterns(self):
        """Анализ паттернов пользователей"""
        try:
            records = self.db.get_all_records(days=30, limit=10000)
            
            if not records:
                return {'error': 'Нет данных для анализа'}
            
            user_activity = {}
            for record in records:
                name = record['full_name']
                user_activity[name] = user_activity.get(name, 0) + 1
            
            # Анализируем паттерны
            active_users = len(user_activity)
            total_actions = len(records)
            
            return {
                'active_users': active_users,
                'total_actions': total_actions,
                'avg_actions_per_user': round(total_actions / active_users, 2) if active_users > 0 else 0
            }
        except Exception as e:
            return {'error': str(e)}
                'db_size_mb': round(db_size / (1024 * 1024), 2),
                'uptime': datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': str(e)}

    async def generate_daily_report(self):
        """Генерация ежедневного отчета"""
        try:
            # Получаем данные за сегодня
            today_records = self.db.get_all_records(days=1, limit=1000)
            current_status = self.db.get_current_status()
            
            report = {
                'date': datetime.now().strftime('%d.%m.%Y'),
                'total_records': len(today_records),
                'current_status': current_status,
                'activity_summary': self._analyze_activity(today_records)
            }
            
            return report
        except Exception as e:
            self.logger.error(f"Ошибка генерации отчета: {e}")
            return None
    
    def _analyze_activity(self, records):
        """Анализ активности"""
        if not records:
            return {'message': 'Нет активности'}
        
        # Группируем по пользователям
        user_activity = {}
        for record in records:
            user_id = record['user_id']
            if user_id not in user_activity:
                user_activity[user_id] = {
                    'name': record['full_name'],
                    'actions': []
                }
            user_activity[user_id]['actions'].append(record['action'])
        
        # Анализируем паттерны
        active_users = len(user_activity)
        total_actions = len(records)
        
        return {
            'active_users': active_users,
            'total_actions': total_actions,
            'avg_actions_per_user': round(total_actions / active_users, 2) if active_users > 0 else 0
        }

# Функция для использования в других модулях
async def get_system_health():
    """Получить состояние системы"""
    monitor = SystemMonitor()
    return await monitor.check_system_health()ystemMonitor()
    return await monitor.check_system_health()

# Пример использования
if __name__ == "__main__":
    async def main():
        monitor = SystemMonitor()
        health = await monitor.check_system_health()
        print("Состояние системы:", health)
        
        report = await monitor.generate_daily_report()
        print("Ежедневный отчет:", report)
    
    asyncio.run(main())
