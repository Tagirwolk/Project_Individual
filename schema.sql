-- ============================================
-- Схема базы данных игрового портала
-- Автор: Набиуллин Тагир
-- Дата: 13.09.2026
-- ============================================

-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица игр
CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    folder_name TEXT NOT NULL
);

-- Таблица рейтингов (связь многие-ко-многим)
CREATE TABLE IF NOT EXISTS ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    game_id INTEGER NOT NULL,
    rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE,
    UNIQUE(user_id, game_id)
);

-- Индексы для ускорения поиска
CREATE INDEX IF NOT EXISTS idx_games_category ON games(category);
CREATE INDEX IF NOT EXISTS idx_ratings_game_id ON ratings(game_id);
CREATE INDEX IF NOT EXISTS idx_ratings_user_id ON ratings(user_id);

-- Тестовые данные (игры)
-- Вставляем игры, только если их ещё нет
INSERT OR IGNORE INTO games (title, category, description, folder_name) 
SELECT * FROM (
    SELECT 'Super Snake', 'Аркада', 'Классическая змейка', 'snake'
    UNION ALL
    SELECT 'Space Shooter', 'Шутер', 'Космическая стрелялка', 'shooter'
    UNION ALL
    SELECT '2048 Puzzle', 'Головоломка', 'Собирай числа', '2048'
) AS temp
WHERE NOT EXISTS (SELECT 1 FROM games);