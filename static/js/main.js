// Глобальные переменные для хранения текущего состояния фильтров
let currentSearch = '';
let currentCategory = '';

// Функция загрузки игр с сервера
async function loadGames() {
    try {
        // Формируем URL с параметрами поиска
        let url = '/api/games?';
        if (currentSearch) {
            url += `search=${encodeURIComponent(currentSearch)}&`;
        }
        if (currentCategory) {
            url += `category=${encodeURIComponent(currentCategory)}`;
        }
        
        // Отправляем запрос к серверу
        const response = await fetch(url);
        const games = await response.json();
        
        // Отрисовываем результаты
        renderGames(games);
    } catch (error) {
        console.error('Ошибка загрузки игр:', error);
    }
}

// Функция отрисовки карточек игр
function renderGames(games) {
    const grid = document.getElementById('gamesGrid');
    const noResults = document.getElementById('noResults');
    
    // Если игр нет, показываем сообщение
    if (games.length === 0) {
        grid.innerHTML = '';
        noResults.style.display = 'block';
        return;
    }
    
    noResults.style.display = 'none';
    
    // Создаем HTML для каждой игры
    grid.innerHTML = games.map(game => `
        <article class="game-card">
            <div class="game-image-placeholder">${game.category}</div>
            <h3>${game.title}</h3>
            <p>${game.description}</p>
            <a href="/game/${game.id}" class="play-btn">Играть</a>
        </article>
    `).join('');
}

// Обработчик ввода в поле поиска
document.getElementById('searchInput').addEventListener('input', (e) => {
    currentSearch = e.target.value;
    loadGames(); // Загружаем игры при каждом изменении текста
});

// Обработчики кликов на кнопки фильтров
document.querySelectorAll('.filter-btn').forEach(button => {
    button.addEventListener('click', (e) => {
        // Убираем активный класс со всех кнопок
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        // Добавляем активный класс на нажатую кнопку
        e.target.classList.add('active');
        
        // Обновляем текущий фильтр и загружаем игры
        currentCategory = e.target.dataset.category;
        loadGames();
    });
});

// Загружаем все игры при загрузке страницы
loadGames();