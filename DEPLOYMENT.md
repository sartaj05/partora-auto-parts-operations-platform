# Deployment Guide

## Fastest local/full-stack demo
With Docker installed:

```bash
docker compose up --build
```

Open `http://localhost:8080`. Nginx serves the React build and proxies `/api/` to Django.

## Frontend-only client demo
The frontend is deliberately resilient. Deploy `frontend/` to a static React host. If no Django API is reachable, login and data modules fall back to local demo records.

Demo credentials:
- `admin@partora.demo` / `demo123`
- `manager@partora.demo` / `demo123`
- `sales@partora.demo` / `demo123`
- `store@partora.demo` / `demo123`

For a connected backend, set:

```env
VITE_API_URL=https://your-api.example.com/api
```

## Backend environment variables
```env
DJANGO_SECRET_KEY=use-a-long-random-secret
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=api.example.com
CORS_ALLOWED_ORIGINS=https://demo.example.com
PARTORA_TOKEN_MAX_AGE=43200
```

## Production notes
- Replace SQLite with PostgreSQL for multi-user production use.
- Use a persistent volume if you keep SQLite for a private demo.
- Set a real Django secret key.
- Restrict allowed hosts and CORS origins.
- Run migrations before serving traffic.
- Replace demo seed accounts before real customer data is added.

## Static host SPA routing
The repository includes a Vercel rewrite file. For Netlify or other static hosts, configure all non-file routes to return `index.html` so `/app/inventory` works after a refresh.
