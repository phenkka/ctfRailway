from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import asyncpg
import os

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/css", StaticFiles(directory="templates/css"), name="css")

DB_USER = os.getenv("POSTGRES_USER")
DB_PASS = os.getenv("POSTGRES_PASSWORD")
DB_NAME = os.getenv("POSTGRES_DB")
DB_HOST = os.getenv("POSTGRES_HOST", "db")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


async def get_db():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        await conn.close()


# --- AUTH ---
ADMIN_LOGIN = "admin"
ADMIN_PASSWORD = "BivaNOrlov2005"


def require_auth(request: Request):
    if request.cookies.get("admin_auth") != "1":
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"},
        )


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if request.query_params.get("debug") == "1":
        resp = RedirectResponse("/logs", status_code=303)
        resp.set_cookie("admin_auth", "1", httponly=True, samesite="lax")
        return resp

    return templates.TemplateResponse("html/login.html", {"request": request})


@app.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    if username == ADMIN_LOGIN and password == ADMIN_PASSWORD:
        resp = RedirectResponse("/logs?debug=0", status_code=303)
        resp.set_cookie("admin_auth", "1", httponly=True, samesite="lax")
        return resp

    return templates.TemplateResponse(
        "html/login.html",
        {"request": request, "error": "Неверный логин или пароль"},
    )


@app.get("/logout")
async def logout():
    resp = RedirectResponse("/login", status_code=303)
    resp.delete_cookie("admin_auth")
    return resp


@app.get("/logs", response_class=HTMLResponse)
async def logs_page(
    request: Request, db=Depends(get_db), _: None = Depends(require_auth)
):
    debug = request.query_params.get("debug")

    if debug == "1":
        pass

    elif debug == "0":
        return templates.TemplateResponse(
            "html/debug_redirect.html", {"request": request}
        )

    rows = await db.fetch(
        """
        SELECT log_id, event_type, action, status_code, created_at, details
        FROM logs
        ORDER BY log_id DESC
        LIMIT 100
    """
    )

    logs = [
        {
            "log_id": r["log_id"],
            "event_type": r["event_type"],
            "action": r["action"],
            "status_code": r["status_code"],
            "created_at": r["created_at"],
            "details": r["details"],
        }
        for r in rows
    ]

    return templates.TemplateResponse(
        "html/logs.html",
        {"request": request, "logs": logs, "limit": 100},
    )


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse("/login")
