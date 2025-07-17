
import logging
import asyncio
from datetime import datetime
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
            'records': await self._check_records()
        }
        return health_report
    
    async def _check_database(self):
        """Проверка состояния БД"""
        try:
            # Простой запрос для проверки подключения
            users = self.db.get_all_users()
            return {
                'status': 'healthy',
                'total_users': len(users) if users else 0
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
                'absent': stats.get('absent', 0)
            }
        except Exception as e:
            self.logger.error(f"Ошибка проверки пользователей: {e}")
            return {'error': str(e)}
    
    async def _check_records(self):
        """Проверка записей"""
        try:
            # Получаем статистику за последние 24 часа
            from datetime import timedelta
            yesterday = datetime.now() - timedelta(days=1)
            
            # Здесь нужен метод для получения записей за период
            return {
                'status': 'checked',
                'note': 'Требуется добавить метод get_records_by_period в DatabaseService'
            }
        except Exception as e:
            return {'error': str(e)}

# Использование:
# monitor = SystemMonitor()
# health = await monitor.check_system_health()
