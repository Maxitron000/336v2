
import asyncio
import logging
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, Any
from services.db_service import DatabaseService
import os

class SystemMonitor:
    def __init__(self):
        self.start_time = datetime.now()
        self.db = DatabaseService()
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'last_error': None,
            'uptime': 0,
            'memory_usage': 0,
            'cpu_usage': 0,
            'active_users': 0,
            'database_size': 0
        }
        
    def get_uptime(self) -> str:
        """Получить время работы системы"""
        uptime = datetime.now() - self.start_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if days > 0:
            return f"{days}д {hours}ч {minutes}м"
        elif hours > 0:
            return f"{hours}ч {minutes}м"
        else:
            return f"{minutes}м {seconds}с"
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Получить системные метрики"""
        try:
            # Использование памяти
            memory = psutil.virtual_memory()
            process = psutil.Process()
            
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Размер базы данных
            db_size = 0
            if os.path.exists('military_tracker.db'):
                db_size = os.path.getsize('military_tracker.db') / (1024 * 1024)  # MB
            
            # Статистика пользователей
            users_count = len(self.db.get_all_users())
            records_count = len(self.db.get_all_records(days=1))
            
            self.metrics.update({
                'uptime': self.get_uptime(),
                'memory_usage': memory.percent,
                'memory_available': memory.available / (1024 * 1024 * 1024),  # GB
                'cpu_usage': cpu_percent,
                'process_memory': process.memory_info().rss / (1024 * 1024),  # MB
                'database_size': round(db_size, 2),
                'total_users': users_count,
                'records_today': records_count
            })
            
            return self.metrics
            
        except Exception as e:
            logging.error(f"Ошибка получения системных метрик: {e}")
            return self.metrics
    
    def increment_request(self, success: bool = True):
        """Увеличить счетчик запросов"""
        self.metrics['total_requests'] += 1
        if success:
            self.metrics['successful_requests'] += 1
        else:
            self.metrics['failed_requests'] += 1
    
    def log_error(self, error: str):
        """Записать ошибку"""
        self.metrics['last_error'] = {
            'message': error,
            'timestamp': datetime.now().isoformat()
        }
        logging.error(f"System error: {error}")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Получить статус здоровья системы"""
        metrics = self.get_system_metrics()
        
        # Определяем статус здоровья
        health_issues = []
        
        if metrics['memory_usage'] > 85:
            health_issues.append("Высокое использование памяти")
        
        if metrics['cpu_usage'] > 80:
            health_issues.append("Высокая нагрузка на CPU")
        
        if metrics['database_size'] > 100:  # Больше 100 MB
            health_issues.append("Большой размер базы данных")
        
        # Проверяем последние ошибки
        if self.metrics['last_error']:
            last_error_time = datetime.fromisoformat(self.metrics['last_error']['timestamp'])
            if (datetime.now() - last_error_time).total_seconds() < 300:  # Последние 5 минут
                health_issues.append("Недавние ошибки в системе")
        
        status = "healthy" if not health_issues else "warning" if len(health_issues) < 3 else "critical"
        
        return {
            'status': status,
            'issues': health_issues,
            'metrics': metrics,
            'timestamp': datetime.now().isoformat()
        }
    
    async def cleanup_if_needed(self):
        """Автоматическая очистка при необходимости"""
        try:
            metrics = self.get_system_metrics()
            
            # Если база данных слишком большая, очищаем старые записи
            if metrics['database_size'] > 50:  # Больше 50 MB
                deleted = self.db.cleanup_old_records(days=90)
                logging.info(f"Автоочистка: удалено {deleted} старых записей")
            
            # Если память заканчивается, оптимизируем базу
            if metrics['memory_usage'] > 80:
                self.db.optimize_database()
                logging.info("Выполнена оптимизация базы данных")
                
        except Exception as e:
            self.log_error(f"Ошибка автоочистки: {e}")

# Глобальный экземпляр монитора
monitor = SystemMonitor()

class AdvancedLogger:
    """Продвинутая система логирования"""
    
    def __init__(self):
        self.setup_logging()
    
    def setup_logging(self):
        """Настройка системы логирования"""
        # Создаем папку для логов
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        # Настройка форматирования
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Основной лог
        main_handler = logging.FileHandler('logs/bot.log', encoding='utf-8')
        main_handler.setFormatter(formatter)
        main_handler.setLevel(logging.INFO)
        
        # Лог ошибок
        error_handler = logging.FileHandler('logs/errors.log', encoding='utf-8')
        error_handler.setFormatter(formatter)
        error_handler.setLevel(logging.ERROR)
        
        # Консольный вывод
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.WARNING)
        
        # Настройка root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(main_handler)
        root_logger.addHandler(error_handler)
        root_logger.addHandler(console_handler)
        
        # Отключаем избыточные логи библиотек
        logging.getLogger('aiogram').setLevel(logging.WARNING)
        logging.getLogger('httpx').setLevel(logging.WARNING)
    
    def log_user_action(self, user_id: int, action: str, details: str = ""):
        """Логирование действий пользователей"""
        logging.info(f"USER_ACTION - ID:{user_id} - {action} - {details}")
    
    def log_admin_action(self, admin_id: int, action: str, details: str = ""):
        """Логирование действий администраторов"""
        logging.info(f"ADMIN_ACTION - ID:{admin_id} - {action} - {details}")
    
    def log_system_event(self, event: str, details: str = ""):
        """Логирование системных событий"""
        logging.info(f"SYSTEM_EVENT - {event} - {details}")
    
    def log_error_with_context(self, error: Exception, context: str = ""):
        """Логирование ошибок с контекстом"""
        logging.error(f"ERROR - {context} - {type(error).__name__}: {str(error)}")
        monitor.log_error(f"{context}: {str(error)}")

# Глобальный экземпляр логгера
advanced_logger = AdvancedLogger()

async def periodic_health_check():
    """Периодическая проверка здоровья системы"""
    while True:
        try:
            health = monitor.get_health_status()
            
            if health['status'] == 'critical':
                advanced_logger.log_system_event(
                    "CRITICAL_HEALTH", 
                    f"Issues: {', '.join(health['issues'])}"
                )
            
            # Автоочистка при необходимости
            await monitor.cleanup_if_needed()
            
            # Ждем 5 минут до следующей проверки
            await asyncio.sleep(300)
            
        except Exception as e:
            advanced_logger.log_error_with_context(e, "periodic_health_check")
            await asyncio.sleep(60)  # При ошибке ждем меньше

def get_system_status() -> str:
    """Получить красивый статус системы для админов"""
    health = monitor.get_health_status()
    metrics = health['metrics']
    
    status_emoji = {
        'healthy': '🟢',
        'warning': '🟡', 
        'critical': '🔴'
    }
    
    status_text = f"{status_emoji[health['status']]} **Статус системы: {health['status'].upper()}**\n\n"
    
    status_text += f"⏱️ **Время работы:** {metrics['uptime']}\n"
    status_text += f"💾 **Память:** {metrics['memory_usage']:.1f}% ({metrics['memory_available']:.1f} GB доступно)\n"
    status_text += f"🖥️ **CPU:** {metrics['cpu_usage']:.1f}%\n"
    status_text += f"🗃️ **База данных:** {metrics['database_size']} MB\n"
    status_text += f"👥 **Всего пользователей:** {metrics['total_users']}\n"
    status_text += f"📊 **Записей сегодня:** {metrics['records_today']}\n\n"
    
    status_text += f"📈 **Статистика запросов:**\n"
    status_text += f"• Всего: {metrics['total_requests']}\n"
    status_text += f"• Успешных: {metrics['successful_requests']}\n"
    status_text += f"• Ошибок: {metrics['failed_requests']}\n"
    
    if health['issues']:
        status_text += f"\n⚠️ **Проблемы:**\n"
        for issue in health['issues']:
            status_text += f"• {issue}\n"
    
    if metrics.get('last_error'):
        last_error = metrics['last_error']
        error_time = datetime.fromisoformat(last_error['timestamp'])
        status_text += f"\n🚨 **Последняя ошибка:**\n"
        status_text += f"• {last_error['message']}\n"
        status_text += f"• {error_time.strftime('%d.%m.%Y %H:%M:%S')}\n"
    
    return status_text
