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
    """API для получения статистики"""
    try:
        # Используем синхронную версию для Flask
        import aiosqlite
        import sqlite3

        # Подключение к базе данных
        conn = sqlite3.connect('military_tracker.db')
        cursor = conn.cursor()

        # Получаем всех пользователей
        cursor.execute("""
            SELECT id, full_name, is_admin FROM users 
            ORDER BY full_name
        """)
        users = cursor.fetchall()

        soldiers = [(u[0], u[1]) for u in users if not u[2]]  # не админы
        admins_count = len([u for u in users if u[2]])  # админы

        present_list = []
        absent_list = []

        # Проверяем статус каждого бойца
        for user_id, full_name in soldiers:
            cursor.execute("""
                SELECT action, location, timestamp FROM user_records 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 1
            """, (user_id,))

            record = cursor.fetchone()

            if record:
                action, location, timestamp = record
                time_str = format_kaliningrad_time(timestamp)

                person_data = {
                    'name': full_name,
                    'location': location,
                    'time': time_str
                }

                if action == 'прибыл':
                    present_list.append(person_data)
                else:
                    absent_list.append(person_data)
            else:
                # Нет записей - считаем отсутствующим
                absent_list.append({
                    'name': full_name,
                    'location': 'Нет данных',
                    'time': '—'
                })

        conn.close()

        # Формируем ответ
        stats = {
            'present': len(present_list),
            'absent': len(absent_list),
            'total': len(soldiers),
            'admins': admins_count,
            'present_list': present_list,
            'absent_list': absent_list,
            'present_count': len(present_list),
            'absent_count': len(absent_list),
            'total_soldiers': len(soldiers),
            'today_records': len(present_list) + len(absent_list),  # Примерное значение
            'last_updated': datetime.now(KALININGRAD_TZ).strftime('%H:%M:%S')
        }

        return jsonify(stats)

    except Exception as e:
        print(f"Ошибка API: {e}")
        return jsonify({
            'present': 0,
            'absent': 0,
            'total': 0,
            'admins': 0,
            'present_list': [],
            'absent_list': [],
            'error': str(e)
        })

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