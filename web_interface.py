
from flask import Flask, render_template, jsonify
import asyncio
from datetime import datetime
import pytz
from services.db_service import DBService
import threading
import time

app = Flask(__name__)

def get_kaliningrad_time():
    """Получить текущее время в Калининграде"""
    tz = pytz.timezone('Europe/Kaliningrad')
    now = datetime.now(tz)
    return {
        'time': now.strftime('%H:%M:%S'),
        'date': now.strftime('%d.%m.%Y'),
        'weekday': now.strftime('%A'),
        'month': now.strftime('%B')
    }

@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')

@app.route('/api/time')
def api_time():
    """API для получения времени"""
    return jsonify(get_kaliningrad_time())

@app.route('/api/stats')
def api_stats():
    """API для получения статистики"""
    try:
        # Получаем статистику из базы данных
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Простая статистика
        stats = {
            'total_users': 0,
            'today_records': 0,
            'online_users': 0
        }
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
