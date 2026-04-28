# Railway deploy

## 1. Create project

1. Open Railway.
2. Create a new project from GitHub.
3. Select this repository.

## 2. Add PostgreSQL

1. In the project, add a PostgreSQL service.
2. In the bot service variables, add:

```env
DATABASE_URL=${{ Postgres.DATABASE_URL }}
BOT_TOKEN=your_telegram_bot_token
```

If the PostgreSQL service has a different name, replace `Postgres` with that service name.

After changing variables in Railway, apply the staged changes and redeploy the bot service.

## 3. Deploy

Railway will use `railway.json`.

Start command:

```bash
python bot.py
```

The bot uses long polling, so it does not need an HTTP port.

## 4. Important

Do not add `.env` to GitHub. Add secrets only in Railway variables.
