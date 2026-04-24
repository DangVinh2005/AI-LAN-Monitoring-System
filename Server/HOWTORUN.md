Run guide (Windows PowerShell)

1. Start Python server (FastAPI)

```powershell
# From repo root
cd python_server

python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
& ".\.venv\Scripts\Activate.ps1"

pip install -r requirements.txt

# Optional (for AI): Ollama
# ollama serve
# ollama pull llama3

# Env vars (match these later in Laravel .env)
$env:ADMIN_API_KEY="A82CE4A67269D7AC52B1A9D695A49"
$env:LARAVEL_WEBHOOK_URL="http://127.0.0.1:8000/webhooks/server-events"
$env:LARAVEL_WEBHOOK_KEY="87C1FE14719ECAA8"

# Run on port 5000 to avoid conflict with Laravel
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

Quick test (new terminal):

```powershell
curl http://127.0.0.1:5000/health
```

2. Start Laravel (Filament Admin + proxy)

````powershell
# From repo root
cd laravel/laravel

# First time setup (if needed)
composer install
copy .env.example .env
php artisan key:generate

# Configure .env to point to Python server and shared keys
# Add/update these lines in .env:
# PY_SERVER_URL=http://127.0.0.1:5000
# ADMIN_API_KEY=A82CE4A67269D7AC52B1A9D695A49
# LARAVEL_WEBHOOK_KEY=87C1FE14719ECAA8

php artisan migrate
php artisan serve    # defaults to http://127.0.0.1:8000
```

Open Filament Admin:

- http://127.0.0.1:8000/admin
  - Sidebar includes: Clients, AI (and you can add more).

Blade UI (demo pages):

- http://127.0.0.1:8000/ui

Troubleshooting:

- If menu/pages not showing, clear caches:

```powershell
php artisan optimize:clear
````

Notes:

- Admin API proxy moved under `/admin-api/*` to avoid conflict with Filament `/admin`.
- Python Admin endpoints require X-API-Key, but Laravel proxy sets it automatically from `ADMIN_API_KEY`.

Linux/Kali server + Windows client quickstart

1. Server on Kali (FastAPI)

```bash
sudo apt update && sudo apt install -y python3 python3-venv python3-pip
cd python_server
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export ADMIN_API_KEY="A82CE4A67269D7AC52B1A9D695A49"
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
# Optional: sudo ufw allow 5000/tcp
# Note your IP from: hostname -I
```

2. Client on Windows (agent)

```powershell
cd client_agent
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

@"
{
  "SERVER_URL": "http://<KALI_IP>:5000",
  "ADMIN_API_KEY": "A82CE4A67269D7AC52B1A9D695A49",
  "POLL_INTERVAL": 5,
  "METRICS_INTERVAL": 30
}
"@ | Set-Content -Encoding UTF8 "$env:APPDATA\agent_demo_config.json"

python agent_demo.py
```
php artisan serve --host 0.0.0.0 --port 8000 
