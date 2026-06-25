# VoiceGuardPay — Backend (FastAPI + Neon Postgres)

Demo-grade auth backend. Deploys to Vercel as serverless functions; runs
locally with `uvicorn`. Same FastAPI `app` object in both cases — see
`api/index.py` for the Vercel entrypoint and `app/main.py` for the real app.

## Folder structure

```
voiceguardpay-backend/
├── api/
│   └── index.py              # Vercel entrypoint only — imports app/main.py
├── app/
│   ├── main.py                # FastAPI() instance, mounts routers, CORS
│   ├── core/
│   │   ├── config.py           # env vars (Settings)
│   │   ├── security.py         # password hashing, JWT
│   │   └── database.py         # async engine/session (Neon)
│   ├── models/
│   │   └── user.py             # SQLAlchemy User model
│   ├── schemas/
│   │   └── auth.py             # Pydantic request/response shapes
│   ├── services/
│   │   └── auth_service.py     # business logic (no FastAPI imports)
│   └── api/
│       ├── deps.py             # get_current_user, etc.
│       └── routes/
│           └── auth.py         # /auth/register, /auth/login, /auth/me
├── migrations/                 # Alembic
├── tests/
├── .env.example
├── requirements.txt
└── vercel.json
```

## 1. Set up Neon

1. Create a project at neon.tech.
2. In the Neon dashboard, open **Connection Details**.
3. Copy the **pooled** connection string (hostname contains `-pooler`) →
   this is `DATABASE_URL`.
4. Copy the **direct** connection string → this is `DATABASE_URL_DIRECT`
   (used only by Alembic migrations).
5. Both need the `postgresql+asyncpg://` prefix (Neon gives you
   `postgresql://` by default — just swap the scheme).

## 2. Local setup

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

copy .env.example .env
# now open .env and fill in: DATABASE_URL, DATABASE_URL_DIRECT, JWT_SECRET_KEY, FRONTEND_ORIGIN
```

Generate a JWT secret:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 3. Run the migration (creates the `users` table)

```powershell
alembic upgrade head
```

This runs against `DATABASE_URL_DIRECT`. If you ever change the `User`
model, generate a new migration with:

```powershell
alembic revision --autogenerate -m "describe your change"
alembic upgrade head
```

## 4. Run locally

```powershell
uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for the interactive Swagger UI — test
`/auth/register` and `/auth/login` directly from there before wiring up
the frontend.

## 5. Deploy to Vercel

```powershell
npm i -g vercel
vercel login
vercel
```

Then in the Vercel dashboard → Project → Settings → Environment Variables,
add: `DATABASE_URL`, `DATABASE_URL_DIRECT`, `JWT_SECRET_KEY`, `JWT_ALGORITHM`,
`ACCESS_TOKEN_EXPIRE_MINUTES`, `FRONTEND_ORIGIN`. Redeploy after adding them
(`vercel --prod`).

Your API will be live at `https://your-project.vercel.app`. Endpoints:

- `POST /auth/register`
- `POST /auth/login`
- `GET  /auth/me` (requires `Authorization: Bearer <token>`)
- `GET  /health`

## 6. Wiring up the Next.js frontend

In your Next.js project's `.env.local`:

```
NEXT_PUBLIC_API_URL=https://your-project.vercel.app
```

Example call from the Login page's `handleLogin`:

```typescript
const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/login`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ email, password }),
});

if (!res.ok) {
  const err = await res.json();
  notify.error(err.detail ?? "Invalid email or password.");
  return;
}

const data = await res.json();
localStorage.setItem("token", data.access_token); // demo-only; consider httpOnly cookies for real auth
notify.success("Logged in successfully.");
```

Same shape for `/auth/register` with `{ name, email, password, confirm_password }`.
