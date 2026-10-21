
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import os

from database.connection import supabase

router = APIRouter(prefix="/attendance", tags=["Attendance"])
security = HTTPBearer()


def current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    try:
        payload = jwt.decode(
            credentials.credentials,
            os.environ["JWT_SECRET"],
            algorithms=["HS256"],
        )
        return payload
    except Exception:
        raise HTTPException(401, "Invalid or expired token")


@router.post("/in")
def attendance_in(user=Depends(current_user)):
    user_id = user["sub"]
    now = datetime.now(timezone.utc)

    # Prevent duplicate open sessions.
    result = (
        supabase.table("user_activity")
        .select("number")
        .eq("user_id", user_id)
        .eq("login", True)
        .eq("logout", False)
        .limit(1)
        .execute()
    )

    if result.data:
        raise HTTPException(409, "Attendance session already exists")

    saved = (
        supabase.table("user_activity")
        .insert({
            "user_id": user_id,
            "login": True,
            "login_time": now.isoformat(),
            "login_date": now.date().isoformat(),
            "logout": False,
            "idle_time_minutes": 0,
            "activity": "PRESENT",
            "created_at": now.isoformat(),
        })
        .execute()
    )

    return {    
        "message": "Attendance PRESENT",
        "user_id": user_id,
        "record": saved.data,
    }


@router.post("/out")
def attendance_out(user_id: str):
    user_id = user_id

    result = (
        supabase.table("user_activity")
        .select("number")
        .eq("user_id", user_id)
        .eq("login", True)
        .eq("logout", False)
        .limit(1)
        .execute()
    )

    now = datetime.now(timezone.utc)

    if not result.data:
        saved = (
            supabase.table("user_activity")
            .insert({
                "user_id": user_id,
                "login": False,
                "login_time": now.isoformat(),
                "login_date": now.date().isoformat(),
                "logout": True,
                "logout_time": now.isoformat(),
                "logout_date": now.date().isoformat(),
                "activity": "LOGOUT",
                "created_at": now.isoformat(),
            })
            .execute()
        )
        return {"message": "Attendance OUT saved", "record": saved.data}

    record_id = result.data[0]["number"]

    saved = (
        supabase.table("user_activity")
        .update({
            "logout": True,
            "logout_time": now.isoformat(),
            "logout_date": now.date().isoformat(),
            "activity": "LOGOUT",
        })
        .eq("number", record_id)
        .execute()
    )

    return {"message": "Attendance OUT saved", "record": saved.data}
