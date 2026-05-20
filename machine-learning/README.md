# world-cup-ml

Monorepo con el modulo ML existente y los nuevos servicios de API y frontend.

## Requisitos

- Python 3.10+
- Node.js 18+

## Backend (FastAPI)

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

## Endpoints

- GET /health
- /api/v1/predict/\*
- /api/v1/stats/\*
