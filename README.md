# Staff Attendance & Monitoring System

A FastAPI-based backend and desktop activity monitoring client for employee attendance and activity tracking.

## Features

- **FastAPI Backend**:
  - Authentication (`/auth`)
  - Attendance check-in/check-out (`/attendance`)
  - Real-time activity & idle monitoring (`/monitoring`)
  - Leave management (`/leave`)
  - Supabase integration for cloud database & authentication
- **Desktop Client**:
  - Background mouse & keyboard activity tracking
  - Idle detection & automated screen lock/black screen
  - Automated sync with backend monitoring endpoints

## Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/61974253/same.git
cd same
```

### 2. Create virtual environment & install dependencies
```bash
python -m venv venv
# On Windows:
.\venv\Scripts\Activate.ps1
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Environment Variables
Copy `.env.example` to `.env` and fill in your Supabase credentials:
```bash
cp .env.example .env
```

### 4. Run the API Server
```bash
uvicorn main:app --reload
```

### 5. Run the Desktop Monitor
```bash
python -m routers.desktop_app.monitor
```
