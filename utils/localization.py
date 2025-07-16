# utils/localization.py
import json
import os

_cache = {}

def get_text(key: str, lang: str = 'ru') -> str:
    if lang not in _cache:
        path = os.path.join(os.path.dirname(__file__), f'../locales/{lang}.json')
        try:
            with open(path, 'r', encoding='utf-8') as f:
                _cache[lang] = json.load(f)
        except Exception:
            _cache[lang] = {}
    return _cache[lang].get(key, key)