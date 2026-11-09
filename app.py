import sqlite3
import os
from flask import Flask, render_template, g, request, jsonify, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'

# Путь к файлу базы данных (будет создан автоматически в папке проекта)
DATABASE = 'database.db'

# Функция для подключения к БД
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row # Позволяет обращаться к колонкам по имени
    return db

# Закрываем соединение после каждого запроса
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Функция для инициализации БД (создаст таблицы, если их нет)
def init_db():
    with app.app_context():
        db = get_db()
        
        # Читаем SQL-скрипт из файла schema.sql
        with app.open_resource('schema.sql', mode='r') as f:
            sql_script = f.read()
        
        # Выполняем весь скрипт целиком
        db.executescript(sql_script)
        print("✅ База данных инициализирована из schema.sql!")

# --- Маршруты (Routes) ---

@app.route('/')
def index():
    db = get_db()
    # Выполняем реальный SQL-запрос к нашей базе данных!
    games = db.execute('SELECT * FROM games').fetchall()
    return render_template('index.html', games=games, page_title='Главная')

@app.route('/game/<int:game_id>')
def play_game(game_id):
    db = get_db()
    game = db.execute('SELECT * FROM games WHERE id = ?', (game_id,)).fetchone()
    
    if game is None:
        return "Игра не найдена", 404
    
    # Получаем средний рейтинг
    rating_data = db.execute('''
        SELECT AVG(rating) as avg_rating, COUNT(*) as total_ratings 
        FROM ratings WHERE game_id = ?
    ''', (game_id,)).fetchone()
    
    avg_rating = rating_data['avg_rating']
    total_ratings = rating_data['total_ratings']
    
    return render_template('game.html', 
                           game=game, 
                           avg_rating=avg_rating, 
                           total_ratings=total_ratings)

# API-маршрут для поиска и фильтрации игр
@app.route('/api/games')
def api_games():
    # Получаем параметры из URL (например, ?search=snake&category=Аркада)
    search_query = request.args.get('search', '').lower()
    category_filter = request.args.get('category', '')
    
    db = get_db()
    
    # Формируем базовый SQL-запрос
    query = 'SELECT * FROM games WHERE 1=1'
    params = []
    
    # Добавляем фильтр по поиску
    if search_query:
        query += ' AND LOWER(title) LIKE ?'
        params.append(f'%{search_query}%')
    
    # Добавляем фильтр по категории
    if category_filter:
        query += ' AND category = ?'
        params.append(category_filter)
    
    # Выполняем запрос
    games = db.execute(query, params).fetchall()
    
    # Преобразуем результаты в список словарей (JSON-формат)
    games_list = []
    for game in games:
        games_list.append({
            'id': game['id'],
            'title': game['title'],
            'category': game['category'],
            'description': game['description'],
            'folder_name': game['folder_name']
        })
    
    # Возвращаем данные в формате JSON
    return jsonify(games_list)

# Декоратор для защиты маршрутов (требует авторизации)
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function
#О проекте
@app.route('/about')
def about():
    return
# Регистрация
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            return render_template('register.html', error='Заполните все поля')
        
        db = get_db()
        # Проверяем, существует ли пользователь
        existing = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
        if existing:
            return render_template('register.html', error='Пользователь уже существует')
        
        # Хешируем пароль (НИКОГДА не храним пароли в открытом виде!)
        password_hash = generate_password_hash(password)
        db.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', 
                   (username, password_hash))
        db.commit()
        
        return redirect('/login')
    
    return render_template('register.html')

# Вход
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        
        if user and check_password_hash(user['password_hash'], password):
            # Сохраняем ID пользователя в сессии
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect('/')
        else:
            return render_template('login.html', error='Неверное имя пользователя или пароль')
    
    return render_template('login.html')

# Выход
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# Поставить оценку игре
@app.route('/rate/<int:game_id>', methods=['POST'])
@login_required
def rate_game(game_id):
    rating = int(request.form.get('rating'))
    user_id = session['user_id']
    
    db = get_db()
    # Проверяем, ставил ли уже этот пользователь оценку
    existing = db.execute('SELECT id FROM ratings WHERE user_id = ? AND game_id = ?', 
                          (user_id, game_id)).fetchone()
    
    if existing:
        # Обновляем оценку
        db.execute('UPDATE ratings SET rating = ? WHERE id = ?', (rating, existing['id']))
    else:
        # Добавляем новую оценку
        db.execute('INSERT INTO ratings (user_id, game_id, rating) VALUES (?, ?, ?)', 
                   (user_id, game_id, rating))
    
    db.commit()
    return redirect(f'/game/{game_id}')

if __name__ == '__main__':
    init_db() # Создаем БД при запуске
    app.run(debug=True, port=5000)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)