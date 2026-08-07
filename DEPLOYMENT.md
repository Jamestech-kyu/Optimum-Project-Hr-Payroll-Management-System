# Deployment Guide

## Backend Environment

Copy `.env.example` to `.env` on the server and replace every placeholder.

Required production values:

- `DEBUG=false`
- `SECRET_KEY`
- `ALLOWED_HOSTS`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `CORS_ALLOWED_ORIGINS`
- `CSRF_TRUSTED_ORIGINS`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`

Use HTTPS in production. Keep these enabled unless your platform handles them
in a documented alternative way:

- `SECURE_SSL_REDIRECT=true`
- `SESSION_COOKIE_SECURE=true`
- `CSRF_COOKIE_SECURE=true`
- `SECURE_HSTS_SECONDS=31536000`

Only set `SECURE_HSTS_PRELOAD=true` after the final domain is confirmed and
you are ready to submit it to the browser preload list.

## Backend Commands

```powershell
venv\Scripts\python.exe -m pip install -r requirements.txt
venv\Scripts\python.exe manage.py migrate
venv\Scripts\python.exe manage.py collectstatic --noinput
venv\Scripts\python.exe manage.py check --deploy
```

Start the Django web process with your production server of choice.

Start the Celery worker:

```powershell
venv\Scripts\python.exe -m celery -A config worker --pool=solo --loglevel=info
```

On Linux, use the default Celery pool unless your host requires `solo`.

## Frontend Environment

In the frontend repo, set:

```env
VITE_API_BASE_URL=https://api.example.com/api
```

Then build:

```powershell
npm.cmd ci
npm.cmd run build
```

Deploy the generated `dist/` folder to your static hosting provider.

## Media Files

Generated reports and payslips are stored under `MEDIA_ROOT`. In production,
configure persistent storage for `media/`, or use a cloud storage backend before
going live.
