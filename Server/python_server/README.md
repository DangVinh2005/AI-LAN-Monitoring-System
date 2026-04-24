Python FastAPI Server

Run

```bash
python -m venv .venv && ./.venv/Scripts/activate 2>nul || source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

Kali Linux quickstart (server-only)

```bash
sudo apt update && sudo apt install -y python3 python3-venv python3-pip
cd python_server
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export ADMIN_API_KEY="A82CE4A67269D7AC52B1A9D695A49"
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
# Optional: sudo ufw allow 5000/tcp
# Get your IP for clients: hostname -I
```

Endpoints

- POST /register
  - body: { client_id, ip?, meta? }
- POST /metrics
  - body: { client_id, ip?, cpu, network_out, connections_per_min, uptime_sec?, meta? }
  - response: { ok, ai: { client_id, status, reason } | null }
- POST /control
  - body: { client_id, action: shutdown|restart|block|notify|unblock, message?, source: Admin|AI, source_user? }
- GET /commands/next?client_id=PC-01
  - response: { command: null | { client_id, action, message?, source } }
- GET /clients
  - query: q?, tag?, blocked?, export?
  - response: JSON list hoặc CSV (khi export=true)
- GET /logs?limit=100

  - query: since_ts?
  - response: recent logs

- GET /health
  - response: { ok, ts }
- GET /stats
  - response: { num_clients, num_blocked, num_queued_commands, last_log_ts, now }
- GET /clients/{client_id}
  - response: details for a single client
- GET /clients/{client_id}/history?limit=100
  - response: recent metric snapshots for the client (up to limit)
- DELETE /clients/{client_id}/history
  - response: { ok, cleared }
- GET /patterns
  - response: { patterns }
- PUT /patterns
  - body: { patterns: { ... } }
  - response: { ok }
- POST /control/bulk
  - body: { client_ids?: string[], action, message?, source?, source_user?, q?, tag?, blocked? }
  - response: { ok, count }
- POST /clients/tags:bulk
- body: { client_ids?: string[], add?: string[], remove?: string[], q?, tag?, blocked? }
- response: { ok, count }
- DELETE /clients/{client_id}
- response: { ok }
- GET /clients/{client_id}/queue
- response: pending commands for a client
- DELETE /clients/{client_id}/queue
- response: { ok, cleared }

AI Integration

- Uses local Ollama daemon (`ollama serve`) and model `llama3` by default.
- Configure in `app/ai.py`.

Storage

- In-memory for active state, with JSONL logs at `python_server/data/logs.jsonl`.

Usage Examples (curl)

```bash
# Health
curl -s http://localhost:5000/health | jq
# From a Windows client, use Kali IP:
# curl -s http://<KALI_IP>:5000/health

# Register a client
curl -s -X POST http://localhost:5000/register \
  -H 'Content-Type: application/json' \
  -d '{"client_id":"PC-01","ip":"192.168.1.10","meta":{"os":"Windows"}}' | jq

# Send metrics (agent heartbeat)
curl -s -X POST http://localhost:5000/metrics \
  -H 'Content-Type: application/json' \
  -d '{"client_id":"PC-01","cpu":32.5,"network_out":120.4,"connections_per_min":15}' | jq

# Get next command for agent
curl -s "http://localhost:5000/commands/next?client_id=PC-01" | jq

# Admin: list clients (requires X-API-Key if ADMIN_API_KEY is set)
curl -s http://localhost:5000/clients -H "X-API-Key: $ADMIN_API_KEY" | jq

# Export CSV
curl -s "http://localhost:5000/clients?export=true" -H "X-API-Key: $ADMIN_API_KEY"

# Admin: single client and history
curl -s http://localhost:5000/clients/PC-01 -H "X-API-Key: $ADMIN_API_KEY" | jq
curl -s "http://localhost:5000/clients/PC-01/history?limit=50" -H "X-API-Key: $ADMIN_API_KEY" | jq
curl -s -X DELETE http://localhost:5000/clients/PC-01/history -H "X-API-Key: $ADMIN_API_KEY" | jq

# Admin: control one client
curl -s -X POST http://localhost:5000/control \
  -H 'Content-Type: application/json' \
  -H "X-API-Key: $ADMIN_API_KEY" \
  -d '{"client_id":"PC-01","action":"notify","message":"Please save work"}' | jq

# Admin: bulk control
curl -s -X POST http://localhost:5000/control/bulk \
  -H 'Content-Type: application/json' \
  -H "X-API-Key: $ADMIN_API_KEY" \
  -d '{"client_ids":["PC-01","PC-02"],"action":"block","message":"Suspicious activity"}' | jq

# Bulk by filters
curl -s -X POST http://localhost:5000/control/bulk \
  -H 'Content-Type: application/json' \
  -H "X-API-Key: $ADMIN_API_KEY" \
  -d '{"q":"PC-","tag":"lab","blocked":false,"action":"notify","message":"Maintenance"}' | jq

# Bulk tags
curl -s -X POST http://localhost:5000/clients/tags:bulk \
  -H 'Content-Type: application/json' \
  -H "X-API-Key: $ADMIN_API_KEY" \
  -d '{"client_ids":["PC-01","PC-02"],"add":["lab"],"remove":["old"]}' | jq

# Admin: patterns get/set
curl -s http://localhost:5000/patterns -H "X-API-Key: $ADMIN_API_KEY" | jq
curl -s -X PUT http://localhost:5000/patterns \
  -H 'Content-Type: application/json' \
  -H "X-API-Key: $ADMIN_API_KEY" \
  -d '{"patterns":{"high_cpu_warn":85,"conn_spike_threshold":3}}' | jq

# Logs and stats
curl -s "http://localhost:5000/logs?limit=50&since_ts=0" -H "X-API-Key: $ADMIN_API_KEY" | jq
curl -s http://localhost:5000/stats -H "X-API-Key: $ADMIN_API_KEY" | jq
```

Admin Auth and Integration

- Set env vars before running:

```bash
set ADMIN_API_KEY=A82CE4A67269D7AC52B1A9D695A49           # Windows PowerShell: $env:ADMIN_API_KEY="A82CE4A67269D7AC52B1A9D695A49"
set LARAVEL_WEBHOOK_URL=https://your-app/webhooks/server-events
set LARAVEL_WEBHOOK_KEY=87C1FE14719ECAA8
```

Notes

- CORS is enabled for all origins to simplify the Admin UI integration.
- AI analysis uses Ollama at `http://localhost:11434`. Start it with `ollama serve` and ensure the `llama3` model is available (or change `MODEL_NAME` in `app/ai.py`).
- Admin endpoints require `X-API-Key` header when `ADMIN_API_KEY` is set.
- Webhooks: Python server POSTs `{ type, data, ts }` to `LARAVEL_WEBHOOK_URL` with optional header `X-Webhook-Key`.
- Additional endpoints: `/ai/health`, `/ai/test` (require `X-API-Key`).
