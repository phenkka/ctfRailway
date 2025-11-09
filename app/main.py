from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from db.pool import init_pool, close_pool
from api.routes import router, frontend_router


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

# Подключаем статические файлы (CSS, JS)
static_dir = Path(__file__).parent / "frontend"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Подключаем все роуты
app.include_router(frontend_router)
app.include_router(router, prefix="/api", tags=["trains"])