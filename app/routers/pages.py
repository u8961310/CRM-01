import uuid

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")

router = APIRouter(tags=["pages"])


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/parents", response_class=HTMLResponse)
async def parents_list(request: Request):
    return templates.TemplateResponse("parents/list.html", {"request": request})


@router.get("/parents/{parent_id}", response_class=HTMLResponse)
async def parent_detail(request: Request, parent_id: uuid.UUID):
    return templates.TemplateResponse("parents/detail.html", {"request": request, "parent_id": str(parent_id)})


@router.get("/students", response_class=HTMLResponse)
async def students_list(request: Request):
    return templates.TemplateResponse("students/list.html", {"request": request})


@router.get("/students/{student_id}", response_class=HTMLResponse)
async def student_detail(request: Request, student_id: uuid.UUID):
    return templates.TemplateResponse("students/detail.html", {"request": request, "student_id": str(student_id)})


@router.get("/info-sessions", response_class=HTMLResponse)
async def info_sessions_list(request: Request):
    return templates.TemplateResponse("info_sessions/list.html", {"request": request})


@router.get("/info-sessions/{session_id}", response_class=HTMLResponse)
async def info_session_detail(request: Request, session_id: uuid.UUID):
    return templates.TemplateResponse("info_sessions/detail.html", {"request": request, "session_id": str(session_id)})
