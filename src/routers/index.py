from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from utils.parse_url import parse_url
from utils.limiter import limiter
from process_query import process_query
from config import MAX_DISPLAY_SIZE, EXAMPLE_REPOS
from utils.log_convert import logSliderToSize


router = APIRouter()
templates = Jinja2Templates(directory="templates")





@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.jinja.html", 
        {
            "request": request,
            "examples": EXAMPLE_REPOS,
            "default_file_size": 243
        }
    )


@router.post("/", response_class=HTMLResponse)
@limiter.limit("10/minute") 
async def index_post(
    request: Request, 
    input_text: str = Form(...),
    max_file_size: int = Form(...)
):
    slider_position = max_file_size
    size_in_kb = logSliderToSize(max_file_size)
    
    try:
        parsed_query = parse_url(input_text, size_in_kb)
        summary, tree, content = await process_query(parsed_query)
    except Exception as e:
        print(e)
        return templates.TemplateResponse(
            "index.jinja.html", 
            {
                "request": request,
                "error_message": f"Error: {e}",
                "examples": EXAMPLE_REPOS,
                "default_file_size": slider_position,  # Return original slider position
                "github_url": input_text  # Add the URL to the error response
            }
        )
    
    if len(content) > MAX_DISPLAY_SIZE:
        content = f"(Files content cropped to {int(MAX_DISPLAY_SIZE/1000)}k characters, download full ingest to see more)\n" + content[:MAX_DISPLAY_SIZE]
    
    return templates.TemplateResponse(
        "index.jinja.html", 
        {
            "request": request, 
            "summary": summary,
            "result": True, 
            "tree": tree, 
            "content": content,
            "examples": EXAMPLE_REPOS,
            "ingest_id": parsed_query['id'],
            "default_file_size": slider_position,  
            "github_url": input_text 
        }
    )



