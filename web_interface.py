
from flask import Flask, render_template_string, jsonify, request
from services.db_service import DatabaseService
from monitoring import monitor, get_system_status
import json
from datetime import datetime
import os

app = Flask(__name__)
db = DatabaseService()

# HTML шаблон для главной страницы
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Военный Табель - Веб Панель</title>
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
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        
        .header h1 {
            color: #2c3e50;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            color: #7f8c8d;
            font-size: 1.2em;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-icon {
            font-size: 2.5em;
            margin-bottom: 15px;
        }
        
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        }
        
        .stat-label {
            color: #7f8c8d;
            font-size: 1em;
        }
        
        .chart-container {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-healthy { background-color: #27ae60; }
        .status-warning { background-color: #f39c12; }
        .status-critical { background-color: #e74c3c; }
        
        .refresh-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1em;
            transition: all 0.3s ease;
            margin: 10px;
        }
        
        .refresh-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        
        .footer {
            text-align: center;
            margin-top: 40px;
            color: #7f8c8d;
        }
        
        .api-section {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            margin-top: 30px;
        }
        
        .api-endpoint {
            background: #f8f9fa;
            padding: 10px 15px;
            border-radius: 8px;
            margin: 10px 0;
            font-family: monospace;
            border-left: 4px solid #667eea;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 20px;
                margin: 10px;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎖️ Военный Табель</h1>
            <p>Система электронного учета военнослужащих</p>
            <button class="refresh-btn" onclick="refreshData()">🔄 Обновить данные</button>
        </div>
        
        <div class="stats-grid" id="statsGrid">
            <!-- Статистика будет загружена через JavaScript -->
        </div>
        
        <div class="chart-container">
            <h3>📊 Системный мониторинг</h3>
            <div id="systemStatus">
                <!-- Статус системы будет загружен через JavaScript -->
            </div>
        </div>
        
        <div class="api-section">
            <h3>🔗 API Endpoints</h3>
            <p>Доступные конечные точки для интеграции:</p>
            <div class="api-endpoint">GET /api/status - Общая статистика</div>
            <div class="api-endpoint">GET /api/users - Список пользователей</div>
            <div class="api-endpoint">GET /api/records - Последние записи</div>
            <div class="api-endpoint">GET /api/health - Системный мониторинг</div>
            <div class="api-endpoint">GET /api/export - Экспорт данных</div>
        </div>
        
        <div class="footer">
            <p>© 2025 Военный Табель. Система работает {{ uptime }}</p>
            <p>Последнее обновление: <span id="lastUpdate">{{ last_update }}</span></p>
        </div>
    </div>

    <script>
        async function loadStats() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                const statsGrid = document.getElementById('statsGrid');
                statsGrid.innerHTML = `
                    <div class="stat-card">
                        <div class="stat-icon">👥</div>
                        <div class="stat-value">${data.total_users}</div>
                        <div class="stat-label">Всего пользователей</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon">✅</div>
                        <div class="stat-value">${data.present_count}</div>
                        <div class="stat-label">В части</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon">❌</div>
                        <div class="stat-value">${data.absent_count}</div>
                        <div class="stat-label">Вне части</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon">📋</div>
                        <div class="stat-value">${data.records_today}</div>
                        <div class="stat-label">Записей сегодня</div>
                    </div>
                `;
                
            } catch (error) {
                console.error('Ошибка загрузки статистики:', error);
            }
        }
        
        async function loadSystemStatus() {
            try {
                const response = await fetch('/api/health');
                const health = await response.json();
                
                const statusClass = `status-${health.status}`;
                const statusIcon = health.status === 'healthy' ? '🟢' : 
                                 health.status === 'warning' ? '🟡' : '🔴';
                
                const systemStatus = document.getElementById('systemStatus');
                systemStatus.innerHTML = `
                    <p><span class="status-indicator ${statusClass}"></span>
                    ${statusIcon} Статус: <strong>${health.status.toUpperCase()}</strong></p>
                    <p>⏱️ Время работы: ${health.metrics.uptime}</p>
                    <p>💾 Использование памяти: ${health.metrics.memory_usage.toFixed(1)}%</p>
                    <p>🖥️ Нагрузка CPU: ${health.metrics.cpu_usage.toFixed(1)}%</p>
                    <p>🗃️ База данных: ${health.metrics.database_size} MB</p>
                    <p>📡 Успешных запросов: ${health.metrics.successful_requests}</p>
                    ${health.issues.length > 0 ? 
                        `<p>⚠️ Проблемы: ${health.issues.join(', ')}</p>` : 
                        '<p>✅ Все системы работают нормально</p>'
                    }
                `;
                
            } catch (error) {
                console.error('Ошибка загрузки статуса системы:', error);
            }
        }
        
        function refreshData() {
            loadStats();
            loadSystemStatus();
            document.getElementById('lastUpdate').textContent = new Date().toLocaleString('ru-RU');
        }
        
        // Загружаем данные при загрузке страницы
        document.addEventListener('DOMContentLoaded', function() {
            refreshData();
            
            // Автообновление каждые 30 секунд
            setInterval(refreshData, 30000);
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Главная страница"""
    uptime = monitor.get_uptime()
    last_update = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
    return render_template_string(HTML_TEMPLATE, uptime=uptime, last_update=last_update)

@app.route('/api/status')
def api_status():
    """API: Общая статистика"""
    try:
        status = db.get_current_status()
        records_today = len(db.get_records_today())
        
        return jsonify({
            'total_users': status['total'],
            'present_count': status['present'],
            'absent_count': status['absent'],
            'records_today': records_today,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users')
def api_users():
    """API: Список пользователей"""
    try:
        users = db.get_all_users()
        return jsonify({
            'users': users,
            'total': len(users),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/records')
def api_records():
    """API: Последние записи"""
    try:
        days = request.args.get('days', 7, type=int)
        limit = request.args.get('limit', 50, type=int)
        
        records = db.get_all_records(days=days, limit=limit)
        return jsonify({
            'records': records,
            'count': len(records),
            'period_days': days,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def api_health():
    """API: Мониторинг системы"""
    try:
        health = monitor.get_health_status()
        return jsonify(health)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export')
def api_export():
    """API: Экспорт данных"""
    try:
        format_type = request.args.get('format', 'json')
        days = request.args.get('days', 30, type=int)
        
        if format_type == 'excel':
            filename = db.export_to_excel(days=days)
            if filename:
                return jsonify({
                    'status': 'success',
                    'filename': filename,
                    'message': 'Excel файл создан'
                })
            else:
                return jsonify({'error': 'Не удалось создать Excel файл'}), 500
                
        else:  # JSON по умолчанию
            records = db.get_all_records(days=days)
            return jsonify({
                'records': records,
                'export_date': datetime.now().isoformat(),
                'period_days': days,
                'total_records': len(records)
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ping')
def api_ping():
    """API: Проверка доступности"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'uptime': monitor.get_uptime()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
