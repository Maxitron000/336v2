"""
Модуль handlers - обработчики команд и сообщений бота
"""

try:
    from . import user, admin, stats, notifications
    __all__ = ['user', 'admin', 'stats', 'notifications']
except ImportError as e:
    print(f"Ошибка импорта модулей handlers: {e}")
    __all__ = []