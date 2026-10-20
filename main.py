
from fastapi import FastAPI

from routers import auth, attendance, monitoring, leave

app = FastAPI(
    title="Staff Attendance Monitoring API",
    version="1.0.0",
)

app.include_router(auth.router)
app.include_router(attendance.router)
app.include_router(monitoring.router)
app.include_router(leave.router)


@app.get("/")
def home():
    return {"message": "Staff Attendance API is running"}
