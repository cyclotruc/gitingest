from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from utils.parse_url import parse_url
from utils.limiter import limiter
from process_query import process_query
from config import MAX_DISPLAY_SIZE, EXAMPLE_REPOS


router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request,
            "examples": EXAMPLE_REPOS
        }
    )


@router.post("/", response_class=HTMLResponse)
@limiter.limit("1/20second") 
async def index_post(request: Request, input_text: str = Form(...)):

    try:
        parsed_url = parse_url(input_text)
        summary, tree, content = await process_query(parsed_url)
    except Exception as e:
        print(e)
        return templates.TemplateResponse(
            "index.html", 
            {
                "request": request,
                "error_message": f"Error: {e}",
                "examples": EXAMPLE_REPOS
            }
        )
    
    if len(content) > MAX_DISPLAY_SIZE:
        content = f"(Files content cropped to {int(MAX_DISPLAY_SIZE/1000)}k characters, download full ingest to see more)\n" + content[:MAX_DISPLAY_SIZE]
        
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request, 
            "summary": summary,
            "result": True, 
            "tree": tree, 
            "content": content,
            "examples": EXAMPLE_REPOS,
            "ingest_id": parsed_url['id']
        }
    )

