from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers import auth, communications, follow_ups, info_sessions, pages, parents, students

app = FastAPI(title="School CRM", version="0.1.0")

# API routers
app.include_router(auth.router)
app.include_router(parents.router)
app.include_router(students.router)
app.include_router(communications.router)
app.include_router(follow_ups.router)
app.include_router(info_sessions.router)

# Page routers (Jinja2 HTML)
app.include_router(pages.router)
