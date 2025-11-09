from pathlib import Path
from typing import List, Optional
from datetime import date, datetime
import pytz
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from api.models import TrainWithRoute
from db.repository import get_trains_with_routes_by_date, get_all_trains_with_routes

router = APIRouter()
frontend_router = APIRouter()


@router.get("/trains", response_model=List[TrainWithRoute])
async def get_trains(
    schedule_date: Optional[date] = Query(None, description="Дата расписания (YYYY-MM-DD). Если не указана, используется текущая дата"),
    train_type: Optional[str] = Query(None, description="Тип поезда для фильтрации"),
    filter_past: bool = Query(True, description="Скрывать прошедшие поезда для текущей даты")
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
        ekb_tz = pytz.timezone('Asia/Yekaterinburg')
        schedule_date = datetime.now(ekb_tz).date()
    
    # Проверяем валидность типа поезда, если указан
    if train_type:
        valid_types = ['suburban', 'express', 'mail', 'long-distance']
        if train_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Неверный тип поезда. Доступные типы: {', '.join(valid_types)}"
            )
    
    # Получаем поезда для указанной даты
    trains = await get_trains_with_routes_by_date(
        schedule_date=schedule_date,
        train_type=train_type,
        filter_past_trains=filter_past
    )
    
    return trains


@router.get("/trains/{train_id}", response_model=TrainWithRoute)
async def get_train(
    train_id: int,
    schedule_date: Optional[date] = Query(None, description="Дата расписания (YYYY-MM-DD)")
) -> TrainWithRoute:
    """
    Получить информацию о конкретном поезде по его ID
    """
    # Если дата не указана, используем текущую дату
    if schedule_date is None:
        ekb_tz = pytz.timezone('Asia/Yekaterinburg')
        schedule_date = datetime.now(ekb_tz).date()
    
    trains = await get_trains_with_routes_by_date(schedule_date=schedule_date, filter_past_trains=False)
    for train in trains:
        if train.train_id == train_id:
            return train
    
    raise HTTPException(
        status_code=404,
        detail=f"Поезд с ID {train_id} не найден для указанной даты"
    )


# Роуты для фронтенда
@frontend_router.get("/")
async def read_root():
    """Главная страница с расписанием поездов"""
    html_file = Path(__file__).parent.parent / "frontend" / "html" / "index.html"
    return FileResponse(html_file)

