
#!/usr/bin/env python3
"""
Скрипт для очистки неиспользуемых файлов проекта
"""
import os

def cleanup_unused_files():
    """Удаляет неиспользуемые файлы"""
    files_to_remove = [
        'handlers.py',  # Старый обработчик
        'keyboards.py',  # Неиспользуемые клавиатуры
    ]
    
    for file in files_to_remove:
        if os.path.exists(file):
            print(f"Удаляем неиспользуемый файл: {file}")
            os.remove(file)
        else:
            print(f"Файл {file} уже отсутствует")

if __name__ == "__main__":
    cleanup_unused_files()
    print("Очистка завершена!")
