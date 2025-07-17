
-- Улучшения для базы данных военного табеля
-- Выполнять эти запросы для оптимизации существующей БД

-- Создание дополнительных индексов для улучшения производительности
CREATE INDEX IF NOT EXISTS idx_records_action ON records (action);
CREATE INDEX IF NOT EXISTS idx_records_location ON records (location);
CREATE INDEX IF NOT EXISTS idx_records_user_timestamp ON records (user_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_users_full_name ON users (full_name);

-- Оптимизация существующих индексов
REINDEX idx_records_user_id;
REINDEX idx_records_timestamp;

-- Создание представления для быстрого доступа к текущему статусу
CREATE VIEW IF NOT EXISTS current_user_status AS
SELECT 
    u.id,
    u.full_name,
    u.username,
    COALESCE(last_record.action, 'не определен') as current_status,
    COALESCE(last_record.location, 'не определено') as current_location,
    COALESCE(last_record.timestamp, u.created_at) as last_activity
FROM users u
LEFT JOIN (
    SELECT DISTINCT 
        r1.user_id,
        r1.action,
        r1.location,
        r1.timestamp
    FROM records r1
    WHERE r1.timestamp = (
        SELECT MAX(r2.timestamp)
        FROM records r2
        WHERE r2.user_id = r1.user_id
    )
) last_record ON u.id = last_record.user_id;

-- Создание таблицы для хранения статистики (опционально)
CREATE TABLE IF NOT EXISTS daily_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL UNIQUE,
    total_users INTEGER NOT NULL,
    present_count INTEGER NOT NULL,
    absent_count INTEGER NOT NULL,
    total_records INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание триггера для автоматического обновления статистики
CREATE TRIGGER IF NOT EXISTS update_daily_stats
AFTER INSERT ON records
BEGIN
    INSERT OR REPLACE INTO daily_stats (
        date, 
        total_users, 
        present_count, 
        absent_count, 
        total_records
    )
    SELECT 
        DATE(NEW.timestamp) as date,
        (SELECT COUNT(*) FROM users) as total_users,
        (SELECT COUNT(*) FROM current_user_status WHERE current_status = 'в части') as present_count,
        (SELECT COUNT(*) FROM current_user_status WHERE current_status = 'не в части') as absent_count,
        (SELECT COUNT(*) FROM records WHERE DATE(timestamp) = DATE(NEW.timestamp)) as total_records;
END;

-- Очистка дубликатов записей (если есть)
DELETE FROM records 
WHERE id NOT IN (
    SELECT MIN(id) 
    FROM records 
    GROUP BY user_id, action, location, timestamp
);

-- Обновление статистики за последние 30 дней
INSERT OR REPLACE INTO daily_stats (date, total_users, present_count, absent_count, total_records)
SELECT 
    DATE(timestamp) as date,
    (SELECT COUNT(*) FROM users) as total_users,
    0 as present_count,  -- Будет обновлено триггером
    0 as absent_count,   -- Будет обновлено триггером
    COUNT(*) as total_records
FROM records 
WHERE DATE(timestamp) >= DATE('now', '-30 days')
GROUP BY DATE(timestamp);

-- Анализ производительности
ANALYZE;

-- Очистка старых записей (старше 6 месяцев)
DELETE FROM records 
WHERE timestamp < datetime('now', '-6 months');

-- Вакуумирование БД для освобождения места
VACUUM;
