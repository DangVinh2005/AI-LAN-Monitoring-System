Server–Client Manager (LAN, Offline)

Overview

An offline LAN system where Admin (Laravel + Filament) and AI (Ollama inside FastAPI) can monitor and control Client Agents. All actions are recorded. Runs fully on local network, no external APIs.

Project structure

```
laravel/         # Admin panel (Filament) – guidance and integration notes
python_server/   # FastAPI + Ollama integration + action logs
client_agent/    # Python agent installed on client machines
```

Quick start

1. Python Server (FastAPI + Ollama)

- Prereqs: Python 3.10+, `ollama` installed and model pulled (e.g., `llama3`)
- Install dependencies and run server:

```bash
cd python_server
python -m venv .venv && ./.venv/Scripts/activate 2>nul || source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

Endpoints (selected)

- POST /register – register a client
- POST /metrics – client sends telemetry; AI may enqueue actions
- POST /control – Admin or AI enqueues commands for a client
- GET /commands/next?client_id=... – client pulls next command
- GET /clients – list registered clients
- GET /logs?limit=100 – recent action logs

2. Client Agent

- Prereqs: Python 3.10+
- Setup and run:

```bash
cd client_agent
python -m venv .venv && ./.venv/Scripts/activate 2>nul || source .venv/bin/activate
pip install -r requirements.txt
python agent_demo.py
```

Agent behavior

- Periodically posts metrics to server and polls next command.
- Executes commands: `screenshot`, `run_cmd`, `notify`, `noop`.
- Cross-platform; configure server URL and API key via env/file.

3. Laravel Admin (Filament)

- See `laravel/README.md` for setup, migrations outline, and example request code from Laravel to FastAPI.

Ollama notes

- The FastAPI server integrates with the local Ollama daemon via the `ollama` Python package. Ensure Ollama is installed and running on the server host, and that the model (e.g., `llama3`) is available.

Security and networking

- Designed for LAN. Protect the FastAPI server with network ACLs and API keys as needed for your environment.

Scenario: Server on Linux (Kali), Client on Windows

1. On Kali (server):

```bash
cd python_server
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export ADMIN_API_KEY="A82CE4A67269D7AC52B1A9D695A49"
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

2. On Windows (client):

```powershell
cd client_agent
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

@"
{
  "SERVER_URL": "http://<KALI_IP>:5000",
  "ADMIN_API_KEY": "A82CE4A67269D7AC52B1A9D695A49"
}
"@ | Set-Content -Encoding UTF8 "$env:APPDATA\agent_demo_config.json"

python agent_demo.py
```
