## Agent Demo (Python)

Cross-platform agent for Server–Client testing: registers to server, sends metrics, polls and executes basic commands, uploads screenshots. Supports Linux (Kali) and Windows.

Safety note: This tool is for lab/testing only. Obtain explicit consent from users before any remote control or screenshot operation. Do not deploy in production without security review.

### Features

- Persistent identity in `~/.agent_demo.json` (Linux) or `%APPDATA%\agent_demo.json` (Windows)
- Registration to server, periodic metrics (CPU, memory, uptime)
- Poll commands: `screenshot`, `run_cmd`, `noop`
- Upload screenshot via multipart
- Rotating logs at `~/.agent_demo.log` or `%APPDATA%\agent_demo.log`
- Graceful shutdown with unregister
- Optional `--dry-run` and a built-in `--stub-server` for local testing

### Quickstart: Server on Kali, Client on Windows

1. Server on Kali (FastAPI)

```bash
cd ../server/python_server
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export ADMIN_API_KEY="A82CE4A67269D7AC52B1A9D695A49"
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
# Note your Kali IP from: hostname -I
```

2. Client on Windows (this agent)

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

Replace `<KALI_IP>` with the actual IP address of your Kali server.

### Requirements

- Python 3.8+
- pip, virtualenv recommended
- Linux (Kali):
  - `apt install -y scrot` (fallback if `mss` unavailable)
  - **VNC Server**: `apt install -y x11vnc` (for remote desktop control)
- Windows:
  - **VNC Server**: Install TightVNC Server from https://www.tightvnc.com/

### Install (Linux/Kali)

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip scrot

cd /opt
sudo mkdir -p /opt/agent_demo
sudo chown "$USER":"$USER" /opt/agent_demo
cd /opt/agent_demo

# Copy files into /opt/agent_demo:
#   agent_demo.py, requirements.txt, agent_demo.service

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Config (optional): ~/.agent_demo_config.json
cat > ~/.agent_demo_config.json << 'EOF'
{
  "SERVER_URL": "http://127.0.0.1:5000",
  "ADMIN_API_KEY": "",

  "POLL_INTERVAL": 5,
  "METRICS_INTERVAL": 30
}
EOF

# Run foreground
python3 agent_demo.py

# Or create systemd service
sudo cp agent_demo.service /etc/systemd/system/agent_demo@.service
echo "SERVER_URL=http://127.0.0.1:5000" | sudo tee /etc/agent_demo.env
# Optional if your server requires it:
# echo "ADMIN_API_KEY=your-admin-key" | sudo tee -a /etc/agent_demo.env
sudo systemctl daemon-reload
sudo systemctl enable agent_demo@$(whoami).service
sudo systemctl start agent_demo@$(whoami).service
sudo systemctl status agent_demo@$(whoami).service
```

### Install (Windows)

```powershell
cd C:\path\to\agent_demo
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

# Optional config at %APPDATA%\agent_demo_config.json
@"
{
  "SERVER_URL": "http://127.0.0.1:5000",
  "ADMIN_API_KEY": "A82CE4A67269D7AC52B1A9D695A49",
  "POLL_INTERVAL": 5,
  "METRICS_INTERVAL": 30
}
"@ | Set-Content -Encoding UTF8 "$env:APPDATA\agent_demo_config.json"

# Run foreground
python agent_demo.py
```

Notes (Windows):

- Screenshot uses `mss` or `Pillow` ImageGrab. On headless sessions, screenshot may fail.
- If `pywin32` is required by your environment, install with `pip install pywin32`.

### Configuration

Config precedence: environment variables > config file > defaults.

Variables:

- `SERVER_URL` (e.g., `http://server:8000`)
- `ADMIN_API_KEY` (required by server)
- `POLL_INTERVAL` (default 5 seconds)
- `METRICS_INTERVAL` (default 30 seconds)

Files:

- Linux: `~/.agent_demo_config.json`
- Windows: `%APPDATA%\agent_demo_config.json`

### Run with stub server (local test)

Terminal 1 (stub server):

```bash
python agent_demo.py --stub-server --server-port 8000
```

Terminal 2 (agent):

```bash
export SERVER_URL=http://127.0.0.1:5000
# Only set if your server enforces admin key
# export ADMIN_API_KEY=your-admin-key
python agent_demo.py
```

Push a command to stub (another terminal):

```bash
curl -s -X POST http://127.0.0.1:8000/stub/push-command \
  -H 'Content-Type: application/json' \
  -d '{"id":"cmd-1","type":"run_cmd","args":{"cmd":"whoami"}}'
```

### systemd service

Install template service and run as your user instance:

```bash
sudo cp agent_demo.service /etc/systemd/system/agent_demo@.service
sudo systemctl daemon-reload
sudo systemctl enable agent_demo@$(whoami).service
sudo systemctl start agent_demo@$(whoami).service
```

Edit `/etc/agent_demo.env` to provide environment variables for the service:

```bash
SERVER_URL=http://127.0.0.1:8000
ADMIN_API_KEY=dev-key
POLL_INTERVAL=5
METRICS_INTERVAL=30
```

### Uninstall

```bash
sudo systemctl stop agent_demo@$(whoami).service || true
sudo systemctl disable agent_demo@$(whoami).service || true
sudo rm -f /etc/systemd/system/agent_demo@.service
sudo systemctl daemon-reload
```

### API contract (expected by agent)

- POST `${SERVER_URL}/register` with `X-API-Key`
- POST `${SERVER_URL}/metrics` with `X-API-Key`
- GET `${SERVER_URL}/commands/next?client_id=...` returns `{ "command": null | { ... } }`
- (Python server variant does not expose `/commands/result`; client will not POST results)
- POST `${SERVER_URL}/agent/upload-screenshot` with `X-API-Key` multipart `screenshot` + `client_id`
- POST `${SERVER_URL}/unregister` with `X-API-Key`
