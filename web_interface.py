
from flask import Flask, render_template_string, jsonify
from services.db_service import DatabaseService
from datetime import datetime
import threading
import asyncio
import os

app = Flask(__name__)
db = DatabaseService()

# HTML шаблон для веб-интерфейса
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎖️ Военный Табель - Панель Мониторинга</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 30px;
            backdrop-filter: blur(10px);
        }
        h1 {
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: rgba(255, 255, 255, 0.2);
            border-radius: 10px;
            padding: 20px;
            text-align: center;
        }
        .stat-number {
            font-size: 3em;
            font-weight: bold;
            margin: 10px 0;
        }
        .stat-label {
            font-size: 1.2em;
            opacity: 0.9;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .online { background-color: #4CAF50; }
        .offline { background-color: #f44336; }
        .refresh-btn {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin: 10px;
        }
        .refresh-btn:hover {
            background: #45a049;
        }
        .last-update {
            text-align: center;
            opacity: 0.8;
            margin-top: 20px;
        }
        .recent-activity {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
        }
        .activity-item {
            padding: 10px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .activity-item:last-child {
            border-bottom: none;
        }
    </style>
    <script>
        function refreshData() {
            location.reload();
        }
        
        // Автообновление каждые 30 секунд
        setInterval(refreshData, 30000);
        
        // Получение статуса бота
        async function checkBotStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                const indicator = document.getElementById('bot-status');
                if (data.status === 'online') {
                    indicator.className = 'status-indicator online';
                } else {
                    indicator.className = 'status-indicator offline';
                }
            } catch (error) {
                document.getElementById('bot-status').className = 'status-indicator offline';
            }
        }
        
        // Проверяем статус при загрузке страницы
        window.onload = checkBotStatus;
    </script>
</head>
<body>
    <div class="container">
        <h1>🎖️ Военный Табель - Панель Мониторинга</h1>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">
                    <span id="bot-status" class="status-indicator online"></span>
                    Статус Бота
                </div>
                <div class="stat-number">ОНЛАЙН</div>
                <div class="stat-label">{{ current_time }}</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-label">👥 Всего пользователей</div>
                <div class="stat-number">{{ stats.total_users }}</div>
                <div class="stat-label">зарегистрировано</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-label">✅ В части</div>
                <div class="stat-number">{{ stats.present }}</div>
                <div class="stat-label">бойцов</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-label">❌ Вне части</div>
                <div class="stat-number">{{ stats.absent }}</div>
                <div class="stat-label">бойцов</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-label">📊 Записей сегодня</div>
                <div class="stat-number">{{ stats.today_records }}</div>
                <div class="stat-label">отметок</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-label">👨‍💼 Администраторов</div>
                <div class="stat-number">{{ stats.admins_count }}</div>
                <div class="stat-label">активных</div>
            </div>
        </div>
        
        <div class="recent-activity">
            <h3>📋 Последняя активность</h3>
            {% for activity in recent_activities %}
            <div class="activity-item">
                <div>
                    <strong>{{ activity.name }}</strong> 
                    {% if activity.action == 'убыл' %}
                        <span style="color: #ff6b6b;">❌ убыл</span>
                    {% else %}
                        <span style="color: #51cf66;">✅ прибыл</span>
                    {% endif %}
                    - {{ activity.location }}
                </div>
                <div style="opacity: 0.8;">{{ activity.time }}</div>
            </div>
            {% endfor %}
        </div>
        
        <div style="text-align: center; margin-top: 30px;">
            <button class="refresh-btn" onclick="refreshData()">🔄 Обновить данные</button>
        </div>
        
        <div class="last-update">
            Последнее обновление: {{ current_time }}
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def dashboard():
    """Главная страница дашборда"""
    try:
        # Получаем статистику
        current_status = db.get_current_status()
        
        # Получаем общую статистику
        total_users = len(db.get_all_users())
        admins_count = len(db.get_all_admins())
        today_records = len(db.get_records_by_date(datetime.now().strftime('%Y-%m-%d')))
        
        # Получаем последнюю активность
        recent_records = db.get_all_records(limit=10)
        recent_activities = []
        
        for record in recent_records:
            user = db.get_user(record['user_id'])
            if user:
                timestamp = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
                recent_activities.append({
                    'name': user['full_name'],
                    'action': record['action'],
                    'location': record['location'],
                    'time': timestamp.strftime('%d.%m %H:%M')
                })
        
        stats = {
            'total_users': total_users,
            'present': current_status['present'],
            'absent': current_status['absent'],
            'today_records': today_records,
            'admins_count': admins_count
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
    """API endpoint для проверки статуса бота"""
    try:
        # Проверяем наличие файла БД как индикатор работы бота
        if os.path.exists('military_tracker.db'):
            return jsonify({'status': 'online', 'timestamp': datetime.now().isoformat()})
        else:
            return jsonify({'status': 'offline', 'timestamp': datetime.now().isoformat()})
    except Exception:
        return jsonify({'status': 'offline', 'timestamp': datetime.now().isoformat()})

@app.route('/api/stats')
def api_stats():
    """API endpoint для получения статистики"""
    try:
        current_status = db.get_current_status()
        total_users = len(db.get_all_users())
        
        return jsonify({
            'total_users': total_users,
            'present': current_status['present'],
            'absent': current_status['absent'],
            'absent_list': current_status['absent_list']
        })
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    print("🌐 Запуск веб-интерфейса мониторинга...")
    print("📊 Панель будет доступна по адресу: http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
