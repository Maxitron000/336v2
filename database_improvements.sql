
-- Добавление индексов для оптимизации запросов
CREATE INDEX IF NOT EXISTS idx_records_user_id ON records(user_id);
CREATE INDEX IF NOT EXISTS idx_records_timestamp ON records(timestamp);
CREATE INDEX IF NOT EXISTS idx_records_action ON records(action);

-- Добавление составных индексов
CREATE INDEX IF NOT EXISTS idx_records_user_timestamp ON records(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_records_action_timestamp ON records(action, timestamp DESC);

-- Проверка целостности данных
PRAGMA foreign_keys = ON;
