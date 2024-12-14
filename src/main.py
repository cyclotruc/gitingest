from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv
from api_analytics.fastapi import Analytics
from starlette.middleware.trustedhost import TrustedHostMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from utils.limiter import limiter
from routers import download, dynamic, index


load_dotenv()

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(Analytics, api_key=os.getenv('API_ANALYTICS_KEY'))
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["gitingest.com", "*.gitingest.com", "gitdigest.dev", "localhost"])
templates = Jinja2Templates(directory="templates")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.head("/")
async def head_root():
    """Mirror the headers and status code of the index page"""
    return HTMLResponse(
        content=None,
        headers={
            "content-type": "text/html; charset=utf-8"
        }
    )
    
@app.get("/api/", response_class=HTMLResponse)
@app.get("/api", response_class=HTMLResponse)
async def api_docs(request: Request):
    return templates.TemplateResponse(
        "api.jinja.html", {"request": request}
    )

@app.get('/favicon.ico')
async def favicon():
    return FileResponse('static/favicon.ico')

@app.get("/robots.txt")
async def robots():
    return FileResponse('static/robots.txt')

app.include_router(index)
app.include_router(download)
app.include_router(dynamic)