
import os
import jwt

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pwdlib import PasswordHash


from database.connection import supabase

router = APIRouter()



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
       


