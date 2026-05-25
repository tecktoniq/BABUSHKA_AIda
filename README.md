# Babushka AIda

Telegram bot for tarot readings powered by aiogram and OpenRouter.

## Environment

Copy `.env.example` to `.env` for local runs, or set these variables in Coolify:

- `BOT_TOKEN`
- `ADMIN_ID`
- `OPENROUTER_API_KEY`
- `MODEL`

## Run with Docker Compose

```bash
docker compose up -d --build
```

The SQLite database is stored in `data_db/babushka_aida.db`. In Coolify, keep the `data_db` volume persistent.
