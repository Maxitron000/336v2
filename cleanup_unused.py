
import os
import logging
from datetime import datetime, timedelta
from services.db_service import DatabaseService

class SystemCleaner:
    def __init__(self):
        self.db = DatabaseService()
        self.logger = logging.getLogger(__name__)
    
    def full_cleanup(self) -> dict:
        """Полная очистка системы"""
        results = {
            'records_deleted': 0,
            'exports_deleted': 0,
            'logs_deleted': 0,
            'temp_files_deleted': 0
        }
        
        try:
            # Очищаем старые записи (старше 6 месяцев)
            results['records_deleted'] = self.db.cleanup_old_records(days=180)
            
            # Очищаем старые экспорты
            results['exports_deleted'] = self.cleanup_old_exports()
            
            # Очищаем старые логи
            results['logs_deleted'] = self.cleanup_old_logs()
            
            # Очищаем временные файлы
            results['temp_files_deleted'] = self.cleanup_temp_files()
            
            self.logger.info(f"Очистка завершена: {results}")
            
        except Exception as e:
            self.logger.error(f"Ошибка при очистке системы: {e}")
            
        return results
    
    def cleanup_old_exports(self) -> int:
        """Очистка старых экспортов"""
        try:
            exports_dir = "exports"
            if not os.path.exists(exports_dir):
                return 0
                
            deleted_count = 0
            cutoff_date = datetime.now() - timedelta(days=30)  # Удаляем файлы старше 30 дней
            
            for filename in os.listdir(exports_dir):
                file_path = os.path.join(exports_dir, filename)
                if os.path.isfile(file_path):
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if file_time < cutoff_date:
                        os.remove(file_path)
                        deleted_count += 1
                        
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Ошибка очистки экспортов: {e}")
            return 0
    
    def cleanup_old_logs(self) -> int:
        """Очистка старых логов"""
        try:
            deleted_count = 0
            cutoff_date = datetime.now() - timedelta(days=7)  # Удаляем логи старше 7 дней
            
            log_patterns = ['*.log', '*.log.*']
            
            for pattern in log_patterns:
                import glob
                for log_file in glob.glob(pattern):
                    if os.path.isfile(log_file):
                        file_time = datetime.fromtimestamp(os.path.getmtime(log_file))
                        if file_time < cutoff_date:
                            os.remove(log_file)
                            deleted_count += 1
                            
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Ошибка очистки логов: {e}")
            return 0
    
    def cleanup_temp_files(self) -> int:
        """Очистка временных файлов"""
        try:
            deleted_count = 0
            temp_patterns = ['*.tmp', '*.temp', '*~', '.#*']
            
            for pattern in temp_patterns:
                import glob
                for temp_file in glob.glob(pattern):
                    if os.path.isfile(temp_file):
                        os.remove(temp_file)
                        deleted_count += 1
                        
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Ошибка очистки временных файлов: {e}")
            return 0
    
    def cleanup_database_only(self) -> int:
        """Очистка только базы данных"""
        try:
            return self.db.cleanup_old_records(days=180)
        except Exception as e:
            self.logger.error(f"Ошибка очистки БД: {e}")
            return 0
    
    def emergency_cleanup(self) -> dict:
        """Экстренная очистка всей системы"""
        results = {
            'total_deleted': 0,
            'database_reset': False,
            'files_deleted': 0
        }
        
        try:
            # Полная очистка базы данных
            results['total_deleted'] = self.db.clear_all_data()
            results['database_reset'] = True
            
            # Удаление всех экспортов
            exports_dir = "exports"
            if os.path.exists(exports_dir):
                import shutil
                shutil.rmtree(exports_dir)
                os.makedirs(exports_dir)
                results['files_deleted'] += 1
                
            self.logger.info(f"Экстренная очистка завершена: {results}")
            
        except Exception as e:
            self.logger.error(f"Ошибка экстренной очистки: {e}")
            
        return results

# Функция для совместимости с существующим кодом
def cleanup_system():
    """Функция для совместимости"""
    cleaner = SystemCleaner()
    return cleaner.full_cleanup()

if __name__ == "__main__":
    # Можно запустить очистку отдельно
    cleaner = SystemCleaner()
    results = cleaner.full_cleanup()
    print(f"Результаты очистки: {results}")
