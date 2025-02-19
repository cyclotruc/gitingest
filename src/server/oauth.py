import os
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth, OAuthError

router = APIRouter()

oauth = OAuth()
oauth.register(
    name="github",
    client_id=os.getenv("GITHUB_CLIENT_ID"),
    client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
    access_token_url="https://github.com/login/oauth/access_token",
    authorize_url="https://github.com/login/oauth/authorize",
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "read:user repo"},
)

@router.get("/login")
async def login(request: Request):
    redirect_uri = request.url_for("auth")
    return await oauth.github.authorize_redirect(request, redirect_uri)

@router.get("/auth")
async def auth(request: Request):
    try:
        token = await oauth.github.authorize_access_token(request)
    except OAuthError as error:
        raise HTTPException(status_code=400, detail=str(error))
    # Get the user's GitHub profile
    user_resp = await oauth.github.get("user", token=token)
    profile = user_resp.json()
    # Store the token in the session so later endpoints can use it
    request.session["github_token"] = token
    # For demonstration, redirect back to home or return profile info
    return RedirectResponse(url="/")

@router.get("/logout")
async def logout(request: Request):
    request.session.pop("github_token", None)
    return RedirectResponse(url="/")
