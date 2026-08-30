"""
auth_routes.py

All the routes this assignment asks for:

    POST /auth/signup           - Stage 1
    POST /auth/login            - Stage 1
    GET  /public/info           - Stage 2
    GET  /protected/profile     - Stage 2 + 3 + 4 (guarded)
    GET  /protected/dashboard   - Stage 4 checkpoint (second guarded route)
    POST /auth/logout           - Stage 4
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from supabase_client import supabase
from auth_guard import get_current_user

router = APIRouter()


class AuthRequest(BaseModel):
    email: EmailStr
    password: str


# ---------- Stage 1: Sign up ----------
@router.post("/auth/signup", status_code=201)
def signup(body: AuthRequest):
    if not body.email or not body.password:
        raise HTTPException(status_code=400, detail={"error": "Email and password are required"})

    try:
        result = supabase.auth.sign_up({"email": body.email, "password": body.password})
    except Exception as e:
        raise HTTPException(status_code=400, detail={"error": str(e)})

    return {"user": result.user}


# ---------- Stage 1: Log in ----------
@router.post("/auth/login")
def login(body: AuthRequest):
    if not body.email or not body.password:
        raise HTTPException(status_code=400, detail={"error": "Email and password are required"})

    try:
        result = supabase.auth.sign_in_with_password(
            {"email": body.email, "password": body.password}
        )
    except Exception:
        raise HTTPException(status_code=401, detail={"error": "Invalid login credentials"})

    return {
        "access_token": result.session.access_token,
        "refresh_token": result.session.refresh_token,
    }


# ---------- Stage 2: Public route ----------
@router.get("/public/info")
def public_info():
    return {"message": "Welcome stranger! This info is public."}


# ---------- Stage 2 + 3 + 4: Protected route ----------
@router.get("/protected/profile")
def profile(current=Depends(get_current_user)):
    user = current["user"]
    return {
        "id": user.id,
        "email": user.email,
        "created_at": user.created_at,
    }


# ---------- Stage 4 checkpoint: a second protected route, same guard ----------
@router.get("/protected/dashboard")
def dashboard(current=Depends(get_current_user)):
    user = current["user"]
    return {"message": f"Welcome back, {user.email}. This is your private dashboard."}


# ---------- Stage 4: Log out ----------
@router.post("/auth/logout", status_code=204)
def logout(current=Depends(get_current_user)):
    try:
        supabase.auth.sign_out(current["token"])
    except Exception:
        pass
    return None