from typing import Optional
from pydantic import BaseModel
from datetime import date


class TrainWithRoute(BaseModel):
    """Модель поезда с информацией о маршруте и времени отправления"""
    train_id: int
    type_train: str  # suburban, express, mail, long-distance
    train_brand: str
    route_id: int
    route_from: str
    route_to: str
    arrival_time: Optional[str]  # Время прибытия может быть NULL
    departure_time: Optional[str]  # Время отправления может быть NULL
    platform: Optional[int]
    schedule_date: date  # Дата расписания
