from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="MyCloudOS Frontend")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        "app.html",
        {
            "request": request,
            "backend_url": "http://127.0.0.1:8009",
        },
    )


@app.get("/verify")
def verify_page(request: Request):
    return templates.TemplateResponse(
        "verify.html",
        {
            "request": request,
            "backend_url": "http://127.0.0.1:8009",
        },
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "mycloudos-frontend"}


@app.get("/dashboard")
def dashboard_redirect() -> RedirectResponse:
    return RedirectResponse(url="/", status_code=302)
