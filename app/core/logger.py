import time
from typing import Optional, Dict, Any
from fastapi import Request
from db.log_repository import create_log
from api.models import LogCreate


async def log_event(
    event_type: str,
    action: str,
    request: Optional[Request] = None,
    details: Optional[Dict[str, Any]] = None,
    status_code: Optional[int] = None,
    execution_time_ms: Optional[int] = None
) -> None:
    ip_address = None
    user_agent = None
    
    if request:
        # Получаем IP адрес клиента
        if request.client:
            ip_address = request.client.host
        # Проверяем заголовки на наличие реального IP (если за прокси)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            ip_address = forwarded_for.split(",")[0].strip()
        
        user_agent = request.headers.get("User-Agent")
    
    log_data = LogCreate(
        event_type=event_type,
        action=action,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
        status_code=status_code,
        execution_time_ms=execution_time_ms
    )
    
    # Асинхронно создаем лог (не ждем завершения)
    await create_log(log_data)


async def request_logger_middleware(request: Request, call_next):
    """
    Middleware для автоматического логирования HTTP запросов.
    Логирует все запросы к API (базовое логирование).
    """
    start_time = time.time()
    
    # Выполняем запрос
    response = await call_next(request)
    
    # Вычисляем время выполнения
    execution_time_ms = int((time.time() - start_time) * 1000)
    
    # Определяем тип события на основе пути
    event_type = "api_request"
    if request.url.path == "/":
        event_type = "page_view"
    elif "/api/trains" in request.url.path:
        if request.url.path.endswith("/trains"):
            event_type = "train_query"
        else:
            event_type = "train_detail_view"
    
    # Формируем описание действия
    action = f"{request.method} {request.url.path}"
    if request.url.query:
        action += f"?{request.url.query}"
    
    # Получаем path_params из scope (если доступны)
    path_params = {}
    try:
        if hasattr(request, 'path_params'):
            path_params = dict(request.path_params)
        elif 'path_params' in request.scope.get('route', {}):
            path_params = dict(request.scope['route'].get('path_params', {}))
    except:
        pass
    
    # Логируем запрос (асинхронно, чтобы не замедлять ответ)
    try:
        await log_event(
            event_type=event_type,
            action=action,
            request=request,
            details={
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "path_params": path_params
            },
            status_code=response.status_code,
            execution_time_ms=execution_time_ms
        )
    except Exception as e:
        # Не прерываем выполнение при ошибке логирования
        print(f"Ошибка логирования в middleware: {e}")
    
    return response

