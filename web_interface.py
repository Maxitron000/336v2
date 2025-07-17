from flask import Flask, render_template_string, jsonify
import os
from datetime import datetime
from services.db_service import DatabaseService

app = Flask(__name__)
db = DatabaseService()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎖️ Электронный Табель - Мониторинг</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 30px;
        }

        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s ease;
        }

        .stat-card:hover {
            transform: translateY(-5px);
        }

        .stat-icon {
            font-size: 3em;
            margin-bottom: 15px;
        }

        .stat-number {
            font-size: 2.5em;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }

        .stat-label {
            font-size: 1.1em;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .present { color: #4CAF50; }
        .absent { color: #f44336; }
        .total { color: #2196F3; }

        .recent-activity {
            padding: 30px;
            background: #f8f9fa;
        }

        .recent-activity h2 {
            margin-bottom: 20px;
            color: #333;
            border-bottom: 3px solid #4facfe;
            padding-bottom: 10px;
        }

        .activity-item {
            background: white;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 10px;
            border-left: 4px solid #4facfe;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }

        .activity-time {
            font-size: 0.9em;
            color: #666;
        }

        .footer {
            background: #333;
            color: white;
            text-align: center;
            padding: 20px;
        }

        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #4CAF50;
            margin-right: 10px;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }

        .refresh-btn {
            background: #4facfe;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            transition: background 0.3s ease;
        }

        .refresh-btn:hover {
            background: #3d8bfe;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎖️ Электронный Табель</h1>
            <p>Рота "В" - Система мониторинга</p>
            <p><span class="status-indicator"></span>Система работает</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon">👥</div>
                <div class="stat-number total">{{ stats.total_users }}</div>
                <div class="stat-label">Всего бойцов</div>
            </div>

            <div class="stat-card">
                <div class="stat-icon">✅</div>
                <div class="stat-number present">{{ stats.present }}</div>
                <div class="stat-label">В части</div>
            </div>

            <div class="stat-card">
                <div class="stat-icon">❌</div>
                <div class="stat-number absent">{{ stats.absent }}</div>
                <div class="stat-label">Отсутствуют</div>
            </div>

            <div class="stat-card">
                <div class="stat-icon">📊</div>
                <div class="stat-number">{{ stats.today_records }}</div>
                <div class="stat-label">Записей сегодня</div>
            </div>
        </div>

        <div class="recent-activity">
            <h2>📝 Последние действия</h2>
            {% for activity in recent_activities %}
            <div class="activity-item">
                <strong>{{ activity.name }}</strong> 
                {% if activity.action == 'в части' %}
                    <span style="color: #4CAF50;">✅ прибыл</span>
                {% else %}
                    <span style="color: #f44336;">❌ убыл</span>
                {% endif %}
                {% if activity.location != 'Часть' %}
                    в {{ activity.location }}
                {% endif %}
                <div class="activity-time">{{ activity.time }}</div>
            </div>
            {% endfor %}
        </div>

        <div class="footer">
            <p>Последнее обновление: {{ current_time }}</p>
            <button class="refresh-btn" onclick="location.reload()">🔄 Обновить</button>
        </div>
    </div>

    <script>
        // Автообновление каждые 30 секунд
        setInterval(function() {
            location.reload();
        }, 30000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Главная страница мониторинга"""
    try:
        # Получаем статистику
        current_status = db.get_current_status()
        all_users = db.get_all_users()

        # Получаем последние записи
        recent_records = db.get_all_records(days=1, limit=10)

        # Форматируем активность
        recent_activities = []
        for record in recent_records:
            recent_activities.append({
                'name': record['full_name'],
                'action': record['action'],
                'location': record['location'],
                'time': datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00')).strftime('%d.%m %H:%M')
            })

        # Считаем записи за сегодня
        today_records = len([r for r in recent_records if datetime.fromisoformat(r['timestamp'].replace('Z', '+00:00')).date() == datetime.now().date()])

        stats = {
            'total_users': len(all_users),
            'present': current_status.get('present', 0),
            'absent': current_status.get('absent', 0),
            'today_records': today_records
        }

        return render_template_string(
            HTML_TEMPLATE,
            stats=stats,
            recent_activities=recent_activities,
            current_time=datetime.now().strftime('%d.%m.%Y %H:%M:%S')
        )

    except Exception as e:
        return f"<h1>Ошибка загрузки данных: {str(e)}</h1>"

@app.route('/api/status')
def api_status():
    """API endpoint для проверки статуса"""
    try:
        stats = db.get_current_status()
        return jsonify({
            'status': 'online',
            'timestamp': datetime.now().isoformat(),
            'data': stats
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)