# Deployment

## Option 1: Full demo stack with Docker

```bash
docker compose up --build
```

Open `http://localhost:8080`. Nginx serves the React build and proxies `/api` to Django. Django migrations and `seed_demo` run when the backend container starts. SQLite data is persisted in the `partora_db` Docker volume.

For any public deployment, replace `DJANGO_SECRET_KEY`, restrict `DJANGO_ALLOWED_HOSTS`, configure HTTPS and move from the demo SQLite setup to a production database when appropriate.

## Option 2: Frontend-only demo

The React frontend contains local demo authentication and fallback data/actions for the operational modules. Build it with:

```bash
cd frontend
npm install
npm run build
```

Deploy `frontend/dist` to Vercel, Netlify, Cloudflare Pages, GitHub Pages (with SPA routing configured), or another static host. If `/api` cannot be reached, the app switches to Demo Mode.

## Option 3: Separate frontend and backend

Set the frontend API URL at build time:

```bash
VITE_API_URL=https://api.example.com/api npm run build
```

Configure the backend environment variables:

```text
DJANGO_DEBUG=0
DJANGO_SECRET_KEY=<strong-random-secret>
DJANGO_ALLOWED_HOSTS=api.example.com
CORS_ALLOWED_ORIGINS=https://app.example.com
DJANGO_DB_PATH=/persistent/path/db.sqlite3
```

## GitHub CI

`.github/workflows/ci.yml` runs Django checks/migrations/seeding and a Vite production build on pushes and pull requests to `main`.
