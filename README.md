# Partora — Auto Parts Operations Demo

Partora is a demo-ready auto-parts / hardware / electrical operations portal built for high-volume inventory search, quotation workflows, stock visibility, and supplier management.

## Stack
- Frontend: React 18 + Vite + React Router
- Backend: Core Django only (no Django REST Framework)
- Database: SQLite for demo; configurable for production
- Auth: Django user + Profile role, signed bearer token returned as JSON
- Demo fallback: the React app automatically switches to local mock data when the backend cannot be reached

## Roles
- Admin — full access
- Manager — inventory, suppliers, quotations, stock overview
- Sales — inventory search and quotations
- Store — inventory and stock movement views

## Demo users
All demo accounts use password `demo123`.
- admin@partora.demo
- manager@partora.demo
- sales@partora.demo
- store@partora.demo

## Quick start
### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

If the Django server is unavailable, the frontend remains usable in Demo Mode with local data and demo login accounts.

## Production build
```bash
cd frontend
npm install
npm run build
```

See `DEPLOYMENT.md` for simple hosting options and environment variables.
