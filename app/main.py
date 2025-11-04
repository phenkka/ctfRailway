from contextlib import asynccontextmanager
from fastapi import FastAPI

from db.pool import init_pool, close_pool
from api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Инициализация при запуске
    await init_pool()
    yield
    # Закрытие при остановке
    await close_pool()


app = FastAPI(
    title="CTF Railway API",
    description="API для получения информации о поездах и расписании",
    version="1.0.0",
    lifespan=lifespan
)

# Подключаем роуты
app.include_router(router, prefix="/api", tags=["trains"])