import os

# Required for local dev: allows OAuth over HTTP (not HTTPS)
os.environ.setdefault('OAUTHLIB_INSECURE_TRANSPORT', '1')

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import uvicorn

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from agent import run_agent

app = FastAPI(title="Life-Ops Calendar Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── OAuth constants ───────────────────────────────────────────────────────────
SCOPES = ['https://www.googleapis.com/auth/calendar']
_SRC_DIR = os.path.join(os.path.dirname(__file__), 'src')
CREDENTIALS_FILE = os.path.join(_SRC_DIR, 'credentials.json')
TOKEN_FILE       = os.path.join(_SRC_DIR, 'token.json')
REDIRECT_URI     = 'http://localhost:8000/auth/callback'
FRONTEND_URL     = 'http://localhost:5173'

# Stores the Flow object between /auth/login and /auth/callback so the
# PKCE code_verifier (generated inside the Flow) is preserved.
_pending_flows: dict[str, Flow] = {}


# ── Schemas ───────────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default_session"


class ChatResponse(BaseModel):
    response: str
    tool_calls: list[str] = []


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "agent": "Life-Ops Calendar Agent"}


# ── Auth: status ──────────────────────────────────────────────────────────────
@app.get("/auth/status")
async def auth_status():
    """Check if a valid Google Calendar token exists."""
    if not os.path.exists(TOKEN_FILE):
        return {"authenticated": False}
    try:
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        if creds.valid:
            return {"authenticated": True}
        # Try to silently refresh an expired token
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_FILE, 'w') as f:
                f.write(creds.to_json())
            return {"authenticated": True}
    except Exception:
        pass
    return {"authenticated": False}


# ── Auth: login ───────────────────────────────────────────────────────────────
@app.get("/auth/login")
async def auth_login():
    """Redirect the user to Google's OAuth consent page."""
    flow = Flow.from_client_secrets_file(
        CREDENTIALS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    auth_url, state = flow.authorization_url(
        access_type='offline',
        prompt='consent',
        include_granted_scopes='true',
    )
    # Persist the Flow so the PKCE code_verifier survives until /auth/callback
    _pending_flows[state] = flow
    return RedirectResponse(url=auth_url)


# ── Auth: callback ────────────────────────────────────────────────────────────
@app.get("/auth/callback")
async def auth_callback(code: str = None, error: str = None, state: str = None):
    """Receive Google's redirect, exchange code for tokens, save, go back to UI."""
    if error:
        return RedirectResponse(url=f"{FRONTEND_URL}?auth_error={error}")
    if not code:
        return RedirectResponse(url=f"{FRONTEND_URL}?auth_error=missing_code")
    try:
        # Reuse the exact Flow from /auth/login so the PKCE code_verifier matches
        flow = _pending_flows.pop(state, None)
        if flow is None:
            return RedirectResponse(url=f"{FRONTEND_URL}?auth_error=session_expired_please_try_again")
        flow.fetch_token(code=code)
        with open(TOKEN_FILE, 'w') as f:
            f.write(flow.credentials.to_json())
        return RedirectResponse(url=f"{FRONTEND_URL}?auth_success=true")
    except Exception as e:
        return RedirectResponse(url=f"{FRONTEND_URL}?auth_error={str(e)}")


# ── Auth: disconnect ──────────────────────────────────────────────────────────
@app.get("/auth/disconnect")
async def auth_disconnect():
    """Delete the stored token to unlink Google Calendar."""
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)
    return {"disconnected": True}


# ── Chat ──────────────────────────────────────────────────────────────────────
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    if not os.path.exists(TOKEN_FILE):
        raise HTTPException(
            status_code=401,
            detail="Google Calendar not connected. Please authenticate first."
        )
    result = await run_in_threadpool(run_agent, request.message, request.thread_id)
    return ChatResponse(**result)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
