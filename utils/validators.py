# utils/validators.py
import re

def validate_full_name(name: str) -> bool:
    return bool(re.match(r'^[А-ЯЁ][а-яё]+ [А-ЯЁ]\\.[А-ЯЁ]\\.$', name))