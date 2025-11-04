from typing import List, Optional
from fastapi import APIRouter, HTTPException

from models import TrainWithRoute
from repository import get_all_trains_with_routes

router = APIRouter()


@router.get("/trains", response_model=List[TrainWithRoute])
async def get_trains(
    train_type: Optional[str] = None
) -> List[TrainWithRoute]:
    """
    Получить список всех поездов с маршрутами и временем отправления.
    
    Можно отфильтровать по типу поезда через query параметр train_type:
    - suburban (пригородные)
    - express (экспресс)
    - mail (почтовые)
    - long-distance (дальнего следования)
    """
    all_trains = await get_all_trains_with_routes()
    
    if train_type:
        # Проверяем валидность типа
        valid_types = ['suburban', 'express', 'mail', 'long-distance']
        if train_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Неверный тип поезда. Доступные типы: {', '.join(valid_types)}"
            )
        return [train for train in all_trains if train.type_train == train_type]
    
    return all_trains


@router.get("/trains/{train_id}", response_model=TrainWithRoute)
async def get_train(train_id: int) -> TrainWithRoute:
    """
    Получить информацию о конкретном поезде по его ID
    """
    all_trains = await get_all_trains_with_routes()
    for train in all_trains:
        if train.train_id == train_id:
            return train
    
    raise HTTPException(
        status_code=404,
        detail=f"Поезд с ID {train_id} не найден"
    )



