from pathlib import Path
from typing import List, Optional
from datetime import date, datetime
import pytz
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse

from api.models import TrainWithRoute
from db.repository import get_trains_with_routes_by_date, get_all_trains_with_routes
from core.logger import log_event
from fastapi.responses import HTMLResponse

router = APIRouter()
frontend_router = APIRouter()


@router.get("/trains", response_model=List[TrainWithRoute])
async def get_trains(
    request: Request,
    schedule_date: Optional[date] = Query(
        None,
        description="Дата расписания (YYYY-MM-DD). Если не указана, используется текущая дата",
    ),
    train_type: Optional[str] = Query(None, description="Тип поезда для фильтрации"),
    filter_past: bool = Query(
        True, description="Скрывать прошедшие поезда для текущей даты"
    ),
) -> List[TrainWithRoute]:
    """
    Получить список всех поездов с маршрутами и временем отправления.

    Параметры:
    - schedule_date: Дата расписания (по умолчанию - текущая дата). Расписание повторяется каждый день.
    - train_type: Фильтр по типу поезда (suburban, express, mail, long-distance)
    - filter_past: Если True, скрывает прошедшие поезда для текущей даты (по умолчанию True)
    """
    # Если дата не указана, используем текущую дату в часовом поясе Екатеринбурга
    if schedule_date is None:
        ekb_tz = pytz.timezone("Asia/Yekaterinburg")
        schedule_date = datetime.now(ekb_tz).date()

    # Проверяем валидность типа поезда, если указан
    if train_type:
        valid_types = ["suburban", "express", "mail", "long-distance"]
        if train_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Неверный тип поезда. Доступные типы: {', '.join(valid_types)}",
            )

    # Получаем поезда для указанной даты
    trains = await get_trains_with_routes_by_date(
        schedule_date=schedule_date,
        train_type=train_type,
        filter_past_trains=filter_past,
    )

    # Дополнительное логирование для фильтров и выбора даты
    event_type = "train_query"
    details = {
        "schedule_date": str(schedule_date),
        "filter_past": filter_past,
        "trains_count": len(trains),
    }

    if train_type:
        event_type = "train_filter"
        details["train_type"] = train_type

    if (
        schedule_date
        and schedule_date != datetime.now(pytz.timezone("Asia/Yekaterinburg")).date()
    ):
        # Если выбрана не текущая дата, логируем как выбор даты
        await log_event(
            event_type="date_select",
            action=f"Выбор даты: {schedule_date}",
            request=request,
            details={"schedule_date": str(schedule_date)},
        )

    await log_event(
        event_type=event_type,
        action=f"Запрос поездов: {len(trains)} найдено",
        request=request,
        details=details,
    )

    return trains


@router.get("/trains/{train_id}", response_model=TrainWithRoute)
async def get_train(
    request: Request,
    train_id: int,
    schedule_date: Optional[date] = Query(
        None, description="Дата расписания (YYYY-MM-DD)"
    ),
) -> TrainWithRoute:
    """
    Получить информацию о конкретном поезде по его ID
    """
    # Если дата не указана, используем текущую дату
    if schedule_date is None:
        ekb_tz = pytz.timezone("Asia/Yekaterinburg")
        schedule_date = datetime.now(ekb_tz).date()

    trains = await get_trains_with_routes_by_date(
        schedule_date=schedule_date, filter_past_trains=False
    )
    for train in trains:
        if train.train_id == train_id:
            # Логируем просмотр деталей поезда
            await log_event(
                event_type="train_detail_view",
                action=f"Просмотр поезда ID: {train_id}",
                request=request,
                details={
                    "train_id": train_id,
                    "train_brand": train.train_brand,
                    "train_type": train.type_train,
                    "schedule_date": str(schedule_date),
                },
            )
            return train

    # Логируем ошибку (поезд не найден)
    await log_event(
        event_type="error",
        action=f"Поезд не найден: ID {train_id}",
        request=request,
        details={"train_id": train_id, "schedule_date": str(schedule_date)},
        status_code=404,
    )

    raise HTTPException(
        status_code=404, detail=f"Поезд с ID {train_id} не найден для указанной даты"
    )


@frontend_router.get("/")
async def read_root(request: Request):
    html_file = Path(__file__).parent.parent / "frontend" / "html" / "index.html"
    html = html_file.read_text(encoding="utf-8")

    await log_event(
        event_type="page_view",
        action="Debug",
        request=request,
        details={
            "status_id": "00000000000000000000140405160901170000000000000000000000002d5f5007384d06310d514d55332f114741451842161b00"
        },
    )

    return HTMLResponse(html)


# Роуты для админки (получение логов)
@router.get("/logs")
async def get_logs(
    request: Request,
    event_type: Optional[str] = Query(None, description="Фильтр по типу события"),
    action: Optional[str] = Query(
        None, description="Фильтр по действию (поиск подстроки)"
    ),
    status_code: Optional[int] = Query(None, description="Фильтр по HTTP статус коду"),
    start_date: Optional[date] = Query(None, description="Начальная дата (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Конечная дата (YYYY-MM-DD)"),
    limit: int = Query(
        100, ge=1, le=1000, description="Максимальное количество записей"
    ),
    offset: int = Query(0, ge=0, description="Смещение для пагинации"),
):
    """
    Получить список логов (для админки).

    Поддерживает фильтрацию по типу события, действию, статус коду и датам.
    """
    from db.log_repository import get_logs, get_logs_count

    # Получаем логи
    logs = await get_logs(
        event_type=event_type,
        action=action,
        status_code=status_code,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )

    # Получаем общее количество для пагинации
    total_count = await get_logs_count(
        event_type=event_type,
        action=action,
        status_code=status_code,
        start_date=start_date,
        end_date=end_date,
    )

    # Логируем запрос к логам
    await log_event(
        event_type="api_request",
        action=f"Получение логов (limit={limit}, offset={offset})",
        request=request,
        details={
            "filters": {
                "event_type": event_type,
                "action": action,
                "status_code": status_code,
                "start_date": str(start_date) if start_date else None,
                "end_date": str(end_date) if end_date else None,
            },
            "total_count": total_count,
            "returned_count": len(logs),
        },
    )

    # Преобразуем в словари для JSON ответа
    return {
        "logs": [log.model_dump() for log in logs],
        "total": total_count,
        "limit": limit,
        "offset": offset,
    }


@router.get("/logs/stats")
async def get_logs_stats(request: Request):
    """
    Получить статистику по логам (для админки).

    Возвращает общее количество логов, статистику по типам событий,
    по статус кодам и другие метрики.
    """
    from db.log_repository import get_logs_count
    from db.pool import get_conn

    # Логируем запрос статистики
    await log_event(
        event_type="api_request", action="Получение статистики логов", request=request
    )

    # Получаем статистику
    total_logs = await get_logs_count()

    # Статистика по типам событий
    event_types = [
        "api_request",
        "page_view",
        "train_query",
        "train_filter",
        "date_select",
        "error",
        "train_detail_view",
    ]
    stats_by_event_type = {}
    for event_type in event_types:
        count = await get_logs_count(event_type=event_type)
        stats_by_event_type[event_type] = count

    # Статистика по статус кодам
    status_codes = [200, 400, 404, 500]
    stats_by_status = {}
    async for conn in get_conn():
        for status_code in status_codes:
            count = await get_logs_count(status_code=status_code)
            stats_by_status[status_code] = count
        break

    # Получаем последние логи для анализа ошибок
    from db.log_repository import get_logs

    recent_errors = await get_logs(event_type="error", limit=10)

    return {
        "total_logs": total_logs,
        "by_event_type": stats_by_event_type,
        "by_status_code": stats_by_status,
        "recent_errors_count": len(recent_errors),
    }
