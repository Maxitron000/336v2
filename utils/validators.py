
# utils/validators.py
import re
import logging

def validate_full_name(name: str) -> tuple[bool, str]:
    """
    Валидация ФИО с детальными проверками
    Возвращает (True/False, сообщение об ошибке)
    """
    if not name or not isinstance(name, str):
        return False, "ФИО не может быть пустым"
    
    name = name.strip()
    
    # Проверка длины
    if len(name) < 5:
        return False, "ФИО слишком короткое (минимум 5 символов)"
    
    if len(name) > 50:
        return False, "ФИО слишком длинное (максимум 50 символов)"
    
    # Проверка на недопустимые символы
    if re.search(r'[0-9<>&"\'`]', name):
        return False, "ФИО не должно содержать цифры или специальные символы"
    
    # Проверка на множественные пробелы
    if re.search(r'\s{2,}', name):
        return False, "ФИО не должно содержать множественные пробелы"
    
    # Основная проверка формата: Фамилия И.О.
    pattern = r'^[А-ЯЁ][а-яё]+ [А-ЯЁ]\.[А-ЯЁ]\.$'
    if not re.match(pattern, name):
        return False, "Неверный формат! Используйте: Фамилия И.О. (например: Иванов И.И.)"
    
    # Дополнительные проверки
    parts = name.split(' ')
    if len(parts) != 2:
        return False, "ФИО должно состоять из фамилии и инициалов через пробел"
    
    surname, initials = parts
    
    # Проверка фамилии
    if len(surname) < 2:
        return False, "Фамилия слишком короткая (минимум 2 символа)"
    
    if len(surname) > 30:
        return False, "Фамилия слишком длинная (максимум 30 символов)"
    
    # Проверка что фамилия содержит только русские буквы
    if not re.match(r'^[А-ЯЁ][а-яё]+$', surname):
        return False, "Фамилия должна содержать только русские буквы и начинаться с заглавной"
    
    # Проверка инициалов
    if not re.match(r'^[А-ЯЁ]\.[А-ЯЁ]\.$', initials):
        return False, "Инициалы должны быть в формате И.О. (заглавные буквы через точку)"
    
    # Проверка на подозрительные комбинации
    suspicious_patterns = [
        r'[аеиоуыэюя]{4,}',  # Слишком много гласных подряд
        r'[бвгджзклмнпрстфхцчшщ]{4,}',  # Слишком много согласных подряд
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, surname.lower()):
            return False, "Фамилия содержит подозрительную комбинацию букв"
    
    # Проверка на запрещенные слова (можно расширить список)
    forbidden_words = ['тест', 'test', 'админ', 'admin', 'бот', 'bot']
    for word in forbidden_words:
        if word in surname.lower():
            return False, f"Фамилия не может содержать слово '{word}'"
    
    return True, ""

def normalize_full_name(name: str) -> str:
    """Нормализация ФИО (удаление лишних пробелов, приведение к правильному регистру)"""
    if not name:
        return ""
    
    # Убираем лишние пробелы
    name = ' '.join(name.split())
    
    # Приводим к правильному регистру
    parts = name.split(' ')
    if len(parts) >= 1:
        # Фамилия: первая буква заглавная, остальные строчные
        surname = parts[0]
        if surname:
            parts[0] = surname[0].upper() + surname[1:].lower()
    
    if len(parts) >= 2:
        # Инициалы: все заглавные
        initials = parts[1]
        parts[1] = initials.upper()
    
    return ' '.join(parts)

def suggest_full_name_correction(name: str) -> str:
    """Предложение исправления для неправильного ФИО"""
    if not name:
        return "Введите ФИО в формате: Фамилия И.О."
    
    # Нормализуем имя
    normalized = normalize_full_name(name)
    
    # Если после нормализации стало валидным
    is_valid, _ = validate_full_name(normalized)
    if is_valid:
        return f"Возможно, вы имели в виду: {normalized}"
    
    # Попытка автокоррекции частых ошибок
    corrected = name.strip()
    
    # Убираем лишние пробелы
    corrected = ' '.join(corrected.split())
    
    # Если нет точек в инициалах, добавляем их
    parts = corrected.split(' ')
    if len(parts) == 2:
        surname, initials_part = parts
        # Если инициалы без точек (например: "ИИ" вместо "И.И.")
        if len(initials_part) == 2 and initials_part.isalpha():
            corrected = f"{surname} {initials_part[0]}.{initials_part[1]}."
    
    # Приводим к правильному регистру
    corrected = normalize_full_name(corrected)
    
    is_valid, _ = validate_full_name(corrected)
    if is_valid:
        return f"Возможно, вы имели в виду: {corrected}"
    
    return "Проверьте формат: Фамилия И.О. (например: Иванов И.И.)"
