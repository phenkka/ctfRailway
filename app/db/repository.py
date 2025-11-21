from typing import List, Optional, Dict
from datetime import date, datetime, time, timedelta
import pytz

from db.pool import get_conn
from api.models import TrainWithRoute


async def get_trains_with_routes_by_date(
    schedule_date: date,
    train_type: Optional[str] = None,
    filter_past_trains: bool = False
) -> List[TrainWithRoute]:
    """
    Получить поезда для указанной даты.
    Расписание повторяется каждый день, поэтому используем данные из БД и добавляем дату.
    
    Args:
        schedule_date: Дата расписания
        train_type: Опциональный фильтр по типу поезда
        filter_past_trains: Если True, фильтрует прошедшие поезда для текущей даты
    """
    # Определяем текущее время в часовом поясе Екатеринбурга (Asia/Yekaterinburg, UTC+5)
    ekb_tz = pytz.timezone('Asia/Yekaterinburg')
    now_ekb = datetime.now(ekb_tz)
    current_date = now_ekb.date()
    current_time = now_ekb.time()
    
    async for conn in get_conn():
        if train_type:
            query = """
                SELECT 
                    t.train_id,
                    t.type_train,
                    t.train_brand,
                    r.route_id,
                    r.route_from,
                    r.route_to,
                    r.arrival_time::text as arrival_time,
                    r.departure_time::text as departure_time,
                    r.platform
                FROM trains t
                INNER JOIN routes r ON t.train_id = r.train_id
                WHERE t.type_train = $1
                ORDER BY COALESCE(r.departure_time, r.arrival_time) ASC
            """
            rows = await conn.fetch(query, train_type)
        else:
            query = """
                SELECT 
                    t.train_id,
                    t.type_train,
                    t.train_brand,
                    r.route_id,
                    r.route_from,
                    r.route_to,
                    r.arrival_time::text as arrival_time,
                    r.departure_time::text as departure_time,
                    r.platform
                FROM trains t
                INNER JOIN routes r ON t.train_id = r.train_id
                ORDER BY COALESCE(r.departure_time, r.arrival_time) ASC
            """
            rows = await conn.fetch(query)
        
        # Подготовка к назначению платформ: формируем упорядоченный список событий
        def parse_time_to_dt(time_str: Optional[str]) -> Optional[datetime]:
            if not time_str:
                return None
            # Ожидаем "HH:MM[:SS]"; используем только часы и минуты
            try:
                parts = time_str.split(':')
                hh = int(parts[0])
                mm = int(parts[1])
                return datetime(schedule_date.year, schedule_date.month, schedule_date.day, hh, mm)
            except Exception:
                return None

        # Платформы 1..10, храним время освобождения каждой
        platform_free_after: Dict[int, datetime] = {p: datetime.min for p in range(1, 11)}

        # Список записей с рассчитанными окнами занятости
        items = []
        for row in rows:
            arr_dt = parse_time_to_dt(row['arrival_time'])
            dep_dt = parse_time_to_dt(row['departure_time'])
            # Окно занятости: 15 минут до и 10 минут после
            if arr_dt and dep_dt:
                window_start = arr_dt - timedelta(minutes=15)
                window_end = dep_dt + timedelta(minutes=10)
            else:
                base_dt = dep_dt or arr_dt
                if base_dt:
                    window_start = base_dt - timedelta(minutes=15)
                    window_end = base_dt + timedelta(minutes=10)
                else:
                    # Если нет ни прибытия, ни отправления — платформу не назначаем
                    window_start = None
                    window_end = None
            # Ключ сортировки — по времени события (departure приоритетно, иначе arrival)
            sort_dt = dep_dt or arr_dt or datetime.max
            items.append({
                'row': row,
                'arr_dt': arr_dt,
                'dep_dt': dep_dt,
                'window_start': window_start,
                'window_end': window_end,
                'sort_dt': sort_dt
            })

        # Они уже отсортированы в SQL по COALESCE(departure, arrival), но дополнительно гарантируем
        items.sort(key=lambda x: x['sort_dt'])

        # Назначаем платформы, избегая конфликтов окон
        assigned_platform_by_route: Dict[int, Optional[int]] = {}
        for it in items:
            row = it['row']
            window_start = it['window_start']
            window_end = it['window_end']
            assigned: Optional[int] = None
            if window_start and window_end:
                # Ищем первую свободную платформу
                for p in range(1, 11):
                    if platform_free_after[p] <= window_start:
                        assigned = p
                        platform_free_after[p] = window_end
                        break
                # Если ни одна не свободна — оставить без платформы (None)
            assigned_platform_by_route[row['route_id']] = assigned

        trains = []
        for row in rows:
            computed_platform = assigned_platform_by_route.get(row['route_id'])
            train = TrainWithRoute(
                train_id=row['train_id'],
                type_train=row['type_train'],
                train_brand=row['train_brand'],
                route_id=row['route_id'],
                route_from=row['route_from'],
                route_to=row['route_to'],
                arrival_time=row['arrival_time'],
                departure_time=row['departure_time'],
                platform=computed_platform,
                schedule_date=schedule_date
            )
            
            # Фильтруем прошедшие поезда только для текущей даты
            if filter_past_trains and schedule_date == current_date:
                # Определяем время поезда:
                # - Если поезд отправляется (есть departure_time), используем его
                # - Если поезд только прибывает (нет departure_time), используем arrival_time
                # - Если оба времени есть (промежуточная станция), используем departure_time
                train_time_str = train.departure_time or train.arrival_time
                if train_time_str:
                    try:
                        # Парсим время из строки "HH:MM:SS" или "HH:MM"
                        time_parts = train_time_str.split(':')
                        hours = int(time_parts[0])
                        minutes = int(time_parts[1])
                        train_time = time(hours, minutes)
                        
                        # Если время поезда уже прошло, пропускаем его
                        if train_time < current_time:
                            continue
                    except (ValueError, IndexError, TypeError):
                        # Если не удалось распарсить время, показываем поезд
                        pass
            
            trains.append(train)
        
        return trains
    return []


async def get_all_trains_with_routes() -> List[TrainWithRoute]:
    """Получить все поезда (для обратной совместимости, использует текущую дату)"""
    current_date = datetime.now(pytz.timezone('Asia/Yekaterinburg')).date()
    return await get_trains_with_routes_by_date(current_date)