"""
auth_guard.py

This is the "guard at the door" -- Stage 3 and Stage 4 of the assignment.

get_current_user() is a FastAPI Dependency. Any route that adds
`user = Depends(get_current_user)` to its function signature automatically
gets protected: FastAPI runs this function FIRST, and only calls your
route's actual code if it doesn't raise an error.
"""

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase_client import supabase

# HTTPBearer is what makes the "Authorize" padlock icon appear in Swagger UI
# (Stage 5). FastAPI uses this to know the route needs a Bearer token.
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)):
    # 1. Was an Authorization header even sent, in the right format?
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail={"error": "Access token required"})

    token = credentials.credentials

    # 2. Ask Supabase: is this token real, or expired/tampered/fake?
    try:
        response = supabase.auth.get_user(token)
    except Exception:
        raise HTTPException(status_code=401, detail={"error": "Invalid or expired token"})

    if not response or not response.user:
        raise HTTPException(status_code=401, detail={"error": "Invalid or expired token"})

    # 3. Token is good -- hand the verified user back to the route.
    #    We also pass the raw token along in case a route (like logout) needs it.
    return {"user": response.user, "token": token}