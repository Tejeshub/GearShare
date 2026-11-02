# GearShare

Production-ready peer-to-peer / boutique cinematic camera & production equipment rental platform.

---

## Repository Structure

```text
GearShare/
├── Frontend/      # Next.js 16 + React 19 + Tailwind CSS + Three.js application
├── Backend/       # FastAPI + SQLAlchemy 2.0 + Alembic + Supabase PostgreSQL
├── AGENTS.md      # Next.js agent notes
├── .gitignore     # Git ignore rules for Frontend and Backend
└── README.md      # Repository overview & startup instructions
```

---

## 1. Frontend Setup & Execution

The frontend is built with **Next.js 16**, **React 19**, **Tailwind CSS**, **Framer Motion**, and **Three.js**.

### Directory
```bash
cd Frontend
```

### Installation
Dependencies are managed via `npm` (matching `package-lock.json`):
```bash
npm install
```

### Running Locally
```bash
npm run dev
```
The frontend starts on `http://localhost:3000`.

### Building for Production
```bash
npm run build
```

---

## 2. Backend Setup & Execution

The backend is built with **FastAPI**, **SQLAlchemy 2.0**, **Pydantic v2**, and connects to a **Supabase PostgreSQL** database.

### Directory
```bash
cd Backend
```

### Environment Configuration
Ensure `Backend/.env` exists (see `Backend/.env.example` for required variables):
```ini
APP_NAME="GearShare API"
APP_ENV="development"
DEBUG=true
DATABASE_URL="postgresql+psycopg://postgres:<PASSWORD>@<HOST>:5432/postgres?sslmode=require"
ALLOWED_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"
```

### Virtual Environment & Dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Running the Backend Server
```bash
uvicorn app.main:app --reload --port 8000
```
- Interactive API Documentation (Swagger): `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/api/v1/health`

### Database Migrations
```bash
alembic current
alembic upgrade head
```

### Database Seeding
```bash
# Seed 8 categories, 12 catalogue products, and 3 Creator Kits
python -m app.db.seed

# Seed 31 physical equipment inventory units
python -m app.db.seed_inventory
```

### Running Tests
```bash
pytest
```
# GearShare
