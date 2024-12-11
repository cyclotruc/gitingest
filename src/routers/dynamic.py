from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from utils.parse_url import parse_url   
from process_query import process_query
from config import MAX_DISPLAY_SIZE
from utils.limiter import limiter


router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/{full_path:path}")
async def catch_all(request: Request, full_path: str):
    return templates.TemplateResponse(
        "github.html",
        {
            "request": request,
            "result": False,
            "loading": True,
            "github_url": f"https://github.com/{full_path}",
        }
    )

@router.post("/{full_path:path}", response_class=HTMLResponse)
@limiter.limit("1/20second") 
async def process_catch_all(request: Request, input_text: str = Form(...)):
    try:
        parsed_url = parse_url(input_text)
        summary, tree, content = await process_query(parsed_url)
    except Exception as e:
        print(e)
        return templates.TemplateResponse(
            "github.html", 
            {
                "request": request, 
                "result": False, 
                "loading": False,
                "error_message": f"Error: \n {e}"
            }
        )

    
    if len(content) > MAX_DISPLAY_SIZE:
        content = f"(Files content cropped to {int(MAX_DISPLAY_SIZE/1000)}k characters, download full digest to see more)\n" + content[:MAX_DISPLAY_SIZE]
        
    return templates.TemplateResponse(
        "github.html", 
        {
            "request": request, 
            "result": True, 
            "loading": False,
            "summary": summary,
            "tree": tree, 
            "content": content,
            "ingest_id": parsed_url["id"]
        }
    )