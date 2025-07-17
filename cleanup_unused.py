import os
import logging
from datetime import datetime, timedelta
from services.db_service import DatabaseService

class SystemCleaner:
    def __init__(self):
        self.db = DatabaseService()
        self.logger = logging.getLogger(__name__)

    def cleanup_old_records(self, days=180):
        """Очистка записей старше указанного количества дней"""
        try:
            deleted_count = self.db.cleanup_old_records(days)
            self.logger.info(f"Удалено старых записей: {deleted_count}")
            return deleted_count
        except Exception as e:
            self.logger.error(f"Ошибка при очистке записей: {e}")
            return 0

    def cleanup_old_exports(self, days=7):
        """Очистка старых экспортированных файлов"""
        try:
            deleted_count = 0
            cutoff_date = datetime.now() - timedelta(days=days)

            # Проверяем папку exports
            exports_dir = "exports"
            if os.path.exists(exports_dir):
                # Ищем файлы экспорта в папке exports
                for filename in os.listdir(exports_dir):
                    if filename.startswith('military_records_') and (filename.endswith('.xlsx') or filename.endswith('.csv')):
                        try:
                            file_path = os.path.join(exports_dir, filename)
                            # Парсим дату из имени файла
                            date_part = filename.replace('military_records_', '').replace('.xlsx', '').replace('.csv', '')
                            if len(date_part) >= 15:  # YYYYMMDD_HHMMSS
                                file_date = datetime.strptime(date_part[-15:], '%Y%m%d_%H%M%S')
                                if file_date < cutoff_date:
                                    os.remove(file_path)
                                    deleted_count += 1
                                    self.logger.info(f"Удален старый экспорт: {file_path}")
                        except Exception as e:
                            self.logger.warning(f"Ошибка при обработке файла {filename}: {e}")

            # Также проверяем корневую папку на случай старых файлов
            for filename in os.listdir('.'):
                if filename.startswith('military_records_') and (filename.endswith('.xlsx') or filename.endswith('.csv')):
                    try:
                        file_stat = os.stat(filename)
                        file_date = datetime.fromtimestamp(file_stat.st_mtime)
                        if file_date < cutoff_date:
                            os.remove(filename)
                            deleted_count += 1
                            self.logger.info(f"Удален старый экспорт из корня: {filename}")
                    except Exception as e:
                        self.logger.warning(f"Ошибка при обработке файла {filename}: {e}")

            return deleted_count
        except Exception as e:
            self.logger.error(f"Ошибка при очистке экспортов: {e}")
            return 0

    def cleanup_logs(self, days=30):
        """Очистка старых логов"""
        try:
            deleted_count = 0
            cutoff_date = datetime.now() - timedelta(days=days)

            # Ищем лог файлы
            for filename in os.listdir('.'):
                if filename.endswith('.log'):
                    try:
                        file_stat = os.stat(filename)
                        file_date = datetime.fromtimestamp(file_stat.st_mtime)

                        if file_date < cutoff_date:
                            os.remove(filename)
                            deleted_count += 1
                            self.logger.info(f"Удален старый лог: {filename}")
                    except Exception as e:
                        self.logger.warning(f"Ошибка при обработке лога {filename}: {e}")

            return deleted_count
        except Exception as e:
            self.logger.error(f"Ошибка при очистке логов: {e}")
            return 0

    def full_cleanup(self):
        """Полная очистка системы"""
        self.logger.info("Начинаем полную очистку системы...")

        results = {
            'records_deleted': self.cleanup_old_records(180),  # 6 месяцев
            'exports_deleted': self.cleanup_old_exports(7),    # 1 неделя
            'logs_deleted': self.cleanup_logs(30)              # 1 месяц
        }

        self.logger.info(f"Очистка завершена: {results}")
        return results

    def get_cleanup_info(self):
        """Получить информацию о том, что можно почистить"""
        try:
            info = {
                'old_records': 0,
                'old_exports': 0,
                'old_logs': 0,
                'total_size_mb': 0
            }

            # Считаем старые записи
            cutoff_date = datetime.now() - timedelta(days=180)
            # Здесь нужно было бы сделать запрос к БД для подсчета

            # Считаем старые экспорты
            export_cutoff = datetime.now() - timedelta(days=7)
            for filename in os.listdir('.'):
                if filename.startswith('military_records_') and filename.endswith('.xlsx'):
                    try:
                        date_part = filename.replace('military_records_', '').replace('.xlsx', '')
                        if len(date_part) >= 15:
                            file_date = datetime.strptime(date_part[:15], '%Y%m%d_%H%M%S')
                            if file_date < export_cutoff:
                                info['old_exports'] += 1
                                info['total_size_mb'] += os.path.getsize(filename) / (1024 * 1024)
                    except:
                        pass

            # Считаем старые логи
            log_cutoff = datetime.now() - timedelta(days=30)
            for filename in os.listdir('.'):
                if filename.endswith('.log'):
                    try:
                        file_stat = os.stat(filename)
                        file_date = datetime.fromtimestamp(file_stat.st_mtime)
                        if file_date < log_cutoff:
                            info['old_logs'] += 1
                            info['total_size_mb'] += os.path.getsize(filename) / (1024 * 1024)
                    except:
                        pass

            info['total_size_mb'] = round(info['total_size_mb'], 2)
            return info

        except Exception as e:
            self.logger.error(f"Ошибка получения информации для очистки: {e}")
            return None

# Запуск если вызван напрямую
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cleaner = SystemCleaner()

    # Показываем что можно почистить
    info = cleaner.get_cleanup_info()
    if info:
        print("Информация для очистки:")
        print(f"- Старых экспортов: {info['old_exports']}")
        print(f"- Старых логов: {info['old_logs']}")
        print(f"- Общий размер: {info['total_size_mb']} MB")

        # Запускаем очистку
        results = cleaner.full_cleanup()
        print(f"\nРезультаты очистки: {results}")
    else:
        print("Ошибка получения информации для очистки")