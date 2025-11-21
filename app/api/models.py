from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import date, datetime


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


class Log(BaseModel):
    """Модель лога событий"""
    log_id: int
    event_type: str  # api_request, page_view, train_query, train_filter, date_select, error, train_detail_view
    action: str
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    status_code: Optional[int] = None
    execution_time_ms: Optional[int] = None
    created_at: datetime


class LogCreate(BaseModel):
    """Модель для создания лога"""
    event_type: str
    action: str
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    status_code: Optional[int] = None
    execution_time_ms: Optional[int] = None
