
import os
import jwt

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pwdlib import PasswordHash

from database.connection import supabase

router = APIRouter(prefix="/auth", tags=["Authentication"])
password_hash = PasswordHash.recommended()

JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET missing in .env")

JWT_ALGORITHM = "HS256"


class LoginRequest(BaseModel):
    user_id: str
    password: str


@router.post("/login")
def login(data: LoginRequest):
    result = (
        supabase.table("users")
        .select("*")
        .eq("user_id", data.user_id)
        .limit(1)
        .execute()
    )

    if not result.data:
        raise HTTPException(401, "Invalid user ID or password")

    user = result.data[0]

    if user.get("is_active") is False:
        raise HTTPException(403, "Account is inactive")
    return {
            "success": True,
            "message": "Login successful",
            "user_id": user["user_id"]
        }


    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": str(user["user_id"]),
            "role": user.get("role", "employee"),
            "iat": now,
            "exp": now + timedelta(hours=8),
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user["user_id"],
        "name": user.get("name", ""),
        "role": user.get("role", "employee"),
    }
