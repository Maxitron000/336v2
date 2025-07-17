
import re
import unicodedata
from typing import Optional

def validate_full_name(full_name: str) -> bool:
    """Валидация ФИО в формате 'Фамилия И.О.'"""
    if not isinstance(full_name, str):
        return False
    
    # Убираем лишние пробелы
    full_name = full_name.strip()
    
    # Проверяем длину
    if len(full_name) < 5 or len(full_name) > 50:
        return False
    
    # Паттерн для проверки формата: Фамилия И.О.
    # Поддерживаем кириллицу и латиницу
    pattern = r'^[А-ЯЁA-Z][а-яёa-z]+\s[А-ЯЁA-Z]\.[А-ЯЁA-Z]\.$'
    
    return bool(re.match(pattern, full_name))

def suggest_full_name_correction(full_name: str) -> Optional[str]:
    """Предложить исправление ФИО"""
    if not isinstance(full_name, str):
        return None
    
    # Убираем лишние пробелы
    full_name = full_name.strip()
    
    if not full_name:
        return None
    
    # Пытаемся автоматически исправить
    parts = full_name.split()
    
    if len(parts) >= 2:
        surname = parts[0]
        rest = ' '.join(parts[1:])
        
        # Исправляем регистр фамилии
        surname = surname.capitalize()
        
        # Пытаемся найти инициалы в остальной части
        initials_match = re.findall(r'[А-ЯЁA-Z]', rest.upper())
        
        if len(initials_match) >= 2:
            # Берем первые две буквы как инициалы
            initial1 = initials_match[0]
            initial2 = initials_match[1]
            corrected = f"{surname} {initial1}.{initial2}."
            
            # Проверяем, что исправленная версия валидна
            if validate_full_name(corrected):
                return corrected
    
    # Если автоисправление не помогло, предлагаем шаблон
    if len(parts) == 1 and len(parts[0]) > 2:
        return f"{parts[0].capitalize()} И.И."
    
    return None

def normalize_full_name(full_name: str) -> str:
    """Нормализация ФИО"""
    if not isinstance(full_name, str):
        return full_name
    
    # Убираем лишние пробелы
    full_name = ' '.join(full_name.split())
    
    # Нормализуем Unicode символы
    full_name = unicodedata.normalize('NFKC', full_name)
    
    return full_name

def validate_location(location: str) -> bool:
    """Валидация локации"""
    if not isinstance(location, str):
        return False
    
    location = location.strip()
    
    # Проверяем длину
    if len(location) < 2 or len(location) > 50:
        return False
    
    # Проверяем на недопустимые символы
    forbidden_chars = ['<', '>', '&', '"', "'", '\n', '\r', '\t']
    if any(char in location for char in forbidden_chars):
        return False
    
    # Проверяем, что не состоит только из пробелов или цифр
    if location.isspace() or location.isdigit():
        return False
    
    return True

def sanitize_input(text: str, max_length: int = 100) -> str:
    """Очистка пользовательского ввода"""
    if not isinstance(text, str):
        return ""
    
    # Убираем лишние пробелы
    text = text.strip()
    
    # Ограничиваем длину
    if len(text) > max_length:
        text = text[:max_length]
    
    # Нормализуем Unicode
    text = unicodedata.normalize('NFKC', text)
    
    # Убираем потенциально опасные символы
    forbidden_chars = ['<', '>', '&', '"', "'"]
    for char in forbidden_chars:
        text = text.replace(char, '')
    
    return text

def validate_time_format(time_str: str) -> bool:
    """Валидация формата времени HH:MM"""
    if not isinstance(time_str, str):
        return False
    
    pattern = r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$'
    return bool(re.match(pattern, time_str))

def validate_user_id(user_id) -> bool:
    """Валидация Telegram user ID"""
    try:
        user_id = int(user_id)
        return 1 <= user_id <= 2147483647  # Максимальный int32
    except (ValueError, TypeError):
        return False

def format_phone_number(phone: str) -> Optional[str]:
    """Форматирование номера телефона"""
    if not isinstance(phone, str):
        return None
    
    # Убираем все нецифровые символы
    digits = re.sub(r'\D', '', phone)
    
    # Проверяем длину
    if len(digits) == 11 and digits.startswith('8'):
        # Заменяем 8 на +7
        return f"+7{digits[1:]}"
    elif len(digits) == 11 and digits.startswith('7'):
        return f"+{digits}"
    elif len(digits) == 10:
        return f"+7{digits}"
    
    return None

def validate_date_string(date_str: str) -> bool:
    """Валидация строки даты в формате DD.MM.YYYY"""
    if not isinstance(date_str, str):
        return False
    
    pattern = r'^([0-2][0-9]|3[01])\.(0[1-9]|1[0-2])\.(\d{4})$'
    match = re.match(pattern, date_str)
    
    if not match:
        return False
    
    day, month, year = map(int, match.groups())
    
    # Базовая проверка дат
    if day < 1 or day > 31:
        return False
    if month < 1 or month > 12:
        return False
    if year < 2020 or year > 2030:  # Разумные границы для военного табеля
        return False
    
    # Проверка дней в месяце
    days_in_month = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if day > days_in_month[month - 1]:
        return False
    
    # Проверка високосного года для февраля
    if month == 2 and day == 29:
        if not (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)):
            return False
    
    return True

def clean_filename(filename: str) -> str:
    """Очистка имени файла от недопустимых символов"""
    if not isinstance(filename, str):
        return "unnamed_file"
    
    # Убираем недопустимые символы для имени файла
    forbidden_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in forbidden_chars:
        filename = filename.replace(char, '_')
    
    # Убираем лишние пробелы и заменяем на подчеркивания
    filename = '_'.join(filename.split())
    
    # Ограничиваем длину
    if len(filename) > 100:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        name = name[:95]
        filename = f"{name}.{ext}" if ext else name
    
    return filename if filename else "unnamed_file"

# Константы для валидации
MAX_USERNAME_LENGTH = 50
MAX_FULL_NAME_LENGTH = 50
MAX_LOCATION_LENGTH = 50
MAX_COMMENT_LENGTH = 200

# Регулярные выражения
TELEGRAM_USERNAME_PATTERN = r'^[a-zA-Z0-9_]{5,32}$'
SAFE_TEXT_PATTERN = r'^[a-zA-Zа-яёА-ЯЁ0-9\s\.\,\!\?\-\(\)]*$'
