from flask import Flask, render_template, jsonify
import asyncio
import threading
from services.db_service import DBService
from datetime import datetime
import pytz

app = Flask(__name__)

# Калининградский часовой пояс
KALININGRAD_TZ = pytz.timezone('Europe/Kaliningrad')

def format_kaliningrad_time(dt_str):
    """Форматирование времени в калининградский часовой пояс"""
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        kld_time = dt.astimezone(KALININGRAD_TZ)
        return kld_time.strftime('%d.%m %H:%M')
    except:
        return dt_str

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stats')
def api_stats():
    """API endpoint для получения статистики"""
    try:
        # Используем синхронную версию
        db = DBService()
        stats = db.get_current_status()

        # Форматируем время для записей
        for category in ['present_list', 'absent_list']:
            if category in stats:
                for person in stats[category]:
                    if 'last_update' in person:
                        person['last_update'] = format_kaliningrad_time(person['last_update'])

        # Добавляем timestamp для кэширования
        stats['timestamp'] = datetime.now().isoformat()

        return jsonify(stats)
    except Exception as e:
        print(f"Ошибка API: {e}")
        return jsonify({
            'error': str(e),
            'total': 0,
            'present': 0,
            'absent': 0,
            'unknown': 0,
            'present_list': [],
            'absent_list': []
        }), 500

def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == '__main__':
    # Запускаем Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    print("🌐 Веб-интерфейс запущен на http://0.0.0.0:5000")
    print("📊 API доступно на http://0.0.0.0:5000/api/stats")

    # Держим главный поток активным
    try:
        while True:
            threading.Event().wait(1)
    except KeyboardInterrupt:
        print("\n🛑 Веб-интерфейс остановлен")