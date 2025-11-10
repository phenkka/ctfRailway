const API_BASE_URL = '/api';

let allTrains = [];
let currentSelectedDate = null;
let currentTrainTypeFilter = '';

// Время сейчас в часовом поясе Екатеринбурга
function getEkbNow() {
    const now = new Date();
    const ekbOffsetMinutes = 5 * 60; // UTC+5
    const localOffsetMinutes = now.getTimezoneOffset(); // в минутах
    return new Date(now.getTime() + (localOffsetMinutes + ekbOffsetMinutes) * 60 * 1000);
}

// Получение текущей даты в часовом поясе Екатеринбурга
function getCurrentDate() {
    const ekbTime = getEkbNow();
    return ekbTime.toISOString().split('T')[0]; // YYYY-MM-DD
}

// Форматирование даты для отображения
function formatDate(dateStr) {
    const date = new Date(dateStr + 'T12:00:00');
    const days = ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'];
    const months = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек'];
    
    const day = date.getDate();
    const dayOfWeek = days[date.getDay()];
    const month = months[date.getMonth()];
    
    const today = getCurrentDate();
    if (dateStr === today) {
        return `Сегодня, ${day} ${month}`;
    }
    
    const tomorrow = new Date(new Date(today + 'T12:00:00').getTime() + 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    if (dateStr === tomorrow) {
        return `Завтра, ${day} ${month}`;
    }
    
    return `${dayOfWeek}, ${day} ${month}`;
}

// Генерация вкладок по дням на месяц вперед
function generateDateTabs() {
    const tabsContainer = document.getElementById('dateTabs');
    const currentDate = getCurrentDate();
    const startDate = new Date(currentDate + 'T12:00:00');
    tabsContainer.innerHTML = '';
    
    // Генерируем вкладки на 30 дней вперед
    for (let i = 0; i < 30; i++) {
        const date = new Date(startDate);
        date.setDate(startDate.getDate() + i);
        const dateStr = date.toISOString().split('T')[0];
        
        const isActive = i === 0; // Первая вкладка (сегодня) активна по умолчанию
        if (isActive) {
            currentSelectedDate = dateStr;
        }
        
        const tab = document.createElement('button');
        tab.className = `date-tab ${isActive ? 'active' : ''}`;
        tab.dataset.date = dateStr;
        tab.textContent = formatDate(dateStr);
        tab.addEventListener('click', () => selectDate(dateStr));
        
        tabsContainer.appendChild(tab);
    }
    
    // Скролл к активной вкладке
    const activeTab = tabsContainer.querySelector('.date-tab.active');
    if (activeTab) {
        setTimeout(() => {
            activeTab.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
        }, 100);
    }
}

// Выбор даты
function selectDate(dateStr) {
    currentSelectedDate = dateStr;
    
    // Обновляем активную вкладку
    document.querySelectorAll('.date-tab').forEach(tab => {
        if (tab.dataset.date === dateStr) {
            tab.classList.add('active');
            tab.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
        } else {
            tab.classList.remove('active');
        }
    });
    
    // Загружаем поезда для выбранной даты
    loadTrains();
}

// Загрузка данных с API
async function loadTrains() {
    const loadingEl = document.getElementById('loading');
    const errorEl = document.getElementById('error');
    const errorMessageEl = document.getElementById('errorMessage');
    const trainsContainer = document.getElementById('trainsContainer');

    loadingEl.style.display = 'block';
    errorEl.style.display = 'none';
    trainsContainer.innerHTML = '';

    try {
        const currentDate = getCurrentDate();
        const selectedDate = currentSelectedDate || currentDate;
        const isToday = selectedDate === currentDate;
        
        // Для текущей даты фильтруем прошедшие поезда, для будущих дат - показываем все
        const filterPast = isToday;
        
        let url = `${API_BASE_URL}/trains?schedule_date=${selectedDate}&filter_past=${filterPast}`;
        
        if (currentTrainTypeFilter) {
            url += `&train_type=${currentTrainTypeFilter}`;
        }
        
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`Ошибка загрузки: ${response.status} ${response.statusText}`);
        }

        allTrains = await response.json();
        displayTrains(allTrains);
    } catch (error) {
        console.error('Ошибка загрузки поездов:', error);
        errorMessageEl.textContent = `Не удалось загрузить расписание: ${error.message}`;
        errorEl.style.display = 'block';
    } finally {
        loadingEl.style.display = 'none';
    }
}

// Отображение поездов
function displayTrains(trains) {
    const trainsContainer = document.getElementById('trainsContainer');

    if (trains.length === 0) {
        const currentDate = getCurrentDate();
        const selectedDate = currentSelectedDate || currentDate;
        const isToday = selectedDate === currentDate;
        
        if (isToday) {
            trainsContainer.innerHTML = '<div class="no-trains">На сегодня рейсов не осталось. Выберите другой день.</div>';
        } else {
            trainsContainer.innerHTML = '<div class="no-trains">На выбранную дату рейсов не найдено</div>';
        }
        return;
    }

    trainsContainer.innerHTML = trains.map(train => createTrainCard(train)).join('');
}

// Создание карточки поезда
function createTrainCard(train) {
    const shouldShowPlat = shouldShowPlatform(train);
    const typeLabels = {
        'suburban': 'Пригородный',
        'express': 'Экспресс',
        'mail': 'Почтовый',
        'long-distance': 'Дальнего следования'
    };

    const typeLabel = typeLabels[train.type_train] || train.type_train;
    const typeClass = train.type_train.replace('-', '-');

    let timeInfo = '';
    
    if (train.arrival_time && train.departure_time) {
        // Промежуточная станция
        timeInfo = `
            <div class="time-info">
                <div class="time-item">
                    <span class="time-label">Прибытие:</span>
                    <span class="time-value">${formatTime(train.arrival_time)}</span>
                </div>
                <div class="time-item">
                    <span class="time-label">Отправление:</span>
                    <span class="time-value">${formatTime(train.departure_time)}</span>
                </div>
            </div>
        `;
    } else if (train.arrival_time) {
        // Только прибытие
        timeInfo = `
            <div class="time-info">
                <div class="time-item">
                    <span class="time-label">Прибытие:</span>
                    <span class="time-value">${formatTime(train.arrival_time)}</span>
                </div>
            </div>
        `;
    } else if (train.departure_time) {
        // Только отправление
        timeInfo = `
            <div class="time-info">
                <div class="time-item">
                    <span class="time-label">Отправление:</span>
                    <span class="time-value">${formatTime(train.departure_time)}</span>
                </div>
            </div>
        `;
    }

    const platformInfo = (train.platform && shouldShowPlat)
        ? `<div class="platform-info">
             <span class="platform-label">Платформа:</span>
             <span class="platform-value">${train.platform}</span>
           </div>`
        : '';

    return `
        <div class="train-card">
            <div class="train-header">
                <div class="train-brand">${train.train_brand}</div>
                <span class="train-type ${typeClass}">${typeLabel}</span>
            </div>
            <div class="route-info">
                <div class="route-item">
                    <div class="route-item-label">Откуда</div>
                    <div class="route-item-value">${train.route_from}</div>
                </div>
                <div class="route-item">
                    <div class="route-item-label">Куда</div>
                    <div class="route-item-value">${train.route_to}</div>
                </div>
            </div>
            ${timeInfo}
            ${platformInfo}
        </div>
    `;
}

// Форматирование времени
function formatTime(timeString) {
    if (!timeString) return '—';
    // Если время в формате "HH:MM:SS", обрезаем до "HH:MM"
    return timeString.substring(0, 5);
}

// Парсинг "HH:MM[:SS]" в объект времени
function parseTimeToHM(timeString) {
    if (!timeString) return null;
    const parts = timeString.split(':');
    const h = parseInt(parts[0], 10);
    const m = parseInt(parts[1], 10);
    if (Number.isNaN(h) || Number.isNaN(m)) return null;
    return { h, m };
}

// Собрать локальный Date в час. поясе Екб для выбранной даты и времени HH:MM
function ekbDateTimeForSelectedDate(timeString) {
    const selectedDate = currentSelectedDate || getCurrentDate();
    const hm = parseTimeToHM(timeString);
    if (!hm) return null;
    // Конструируем как если бы это локальная дата в Екб
    // Используем компоненты, чтобы избежать влияния локальной TZ: создадим ISO и потом поправим в getEkbNow сравнением в том же "Екб-времени"
    const [year, month, day] = selectedDate.split('-').map(n => parseInt(n, 10));
    // Создаем дату в "локальном" времени текущей среды, но мы сравниваем с getEkbNow(), который тоже приведен к Екб, так что достаточно согласованности
    return new Date(year, month - 1, day, hm.h, hm.m, 0, 0);
}

// Показывать ли платформу: только за 15 минут до события и 10 минут после
// Правила:
// - Если есть arrival и departure: окно [arrival - 15m ; departure + 10m]
// - Иначе: одно событие (arr или dep): окно [event - 15m ; event + 10m]
// - Для не сегодняшней даты окно не наступит "сейчас", так что платформа скрыта
function shouldShowPlatform(train) {
    // Без платформы показывать нечего
    if (!train.platform) return false;
    const nowEkb = getEkbNow();
    const currentDate = getCurrentDate();
    const selectedDate = currentSelectedDate || currentDate;
    // Скрываем для дат не сегодня — пользователь увидит платформу лишь в реальном окне
    if (selectedDate !== currentDate) return false;

    const arrDt = train.arrival_time ? ekbDateTimeForSelectedDate(train.arrival_time) : null;
    const depDt = train.departure_time ? ekbDateTimeForSelectedDate(train.departure_time) : null;

    let windowStart = null;
    let windowEnd = null;

    if (arrDt && depDt) {
        windowStart = new Date(arrDt.getTime() - 15 * 60 * 1000);
        windowEnd = new Date(depDt.getTime() + 10 * 60 * 1000);
    } else {
        const base = depDt || arrDt;
        if (!base) return false;
        windowStart = new Date(base.getTime() - 15 * 60 * 1000);
        windowEnd = new Date(base.getTime() + 10 * 60 * 1000);
    }

    return nowEkb >= windowStart && nowEkb <= windowEnd;
}

// Фильтрация поездов
function filterTrains() {
    currentTrainTypeFilter = document.getElementById('trainTypeFilter').value;
    loadTrains();
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    // Генерируем вкладки по дням
    generateDateTabs();
    
    // Загружаем поезда для текущей даты
    loadTrains();

    // Настраиваем фильтр
    document.getElementById('trainTypeFilter').addEventListener('change', filterTrains);

    // Настраиваем кнопку обновления
    document.getElementById('refreshBtn').addEventListener('click', () => {
        currentTrainTypeFilter = '';
        document.getElementById('trainTypeFilter').value = '';
        loadTrains();
    });
});
