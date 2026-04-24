# AI LAN Monitoring System

An AI-powered LAN monitoring and remote control system for centralized management of multiple clients in a local network.

The system combines real-time telemetry, remote command execution, and AI-based anomaly detection, running fully offline without cloud dependencies.

---

## 🚀 Key Features

- Centralized Monitoring  
- Remote Control  
- AI-based Anomaly Detection (Ollama)  
- Secure Communication (API key, logging)  
- Fault-tolerant Design  
- Fully Offline (LAN)

---

## 🏗️ Architecture

Admin Panel (Laravel + Filament)
        ↓
FastAPI Server (AI + Logic)
        ↓
Client Agents (Python)

---

## 📁 Project Structure

```text
ai-lan-monitoring-system/
├── server/       # FastAPI backend + AI
├── client/       # Python agent
├── admin/        # Laravel dashboard
└── README.md
```

---

## ⚡ Quick Start

### 1. Start Server
```text
cd server
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export ADMIN_API_KEY="dev-key"
uvicorn app.main:app --host 0.0.0.0 --port 5000
```
---

### 2. Run Client
```text

cd client
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python agent_demo.py

Config:
{
  "SERVER_URL": "http://<SERVER_IP>:5000",
  "ADMIN_API_KEY": "dev-key"
}
```
---

### 3. Admin Dashboard
```text
cd admin
composer install
php artisan serve

http://localhost:8000
```
---

## 🔌 Core API

POST /register  
POST /metrics  
POST /control  
GET /commands/next  
GET /clients  
GET /logs  

---

## 🔐 Security

- API key authentication  
- Role separation (Admin / AI)  
- Full audit logging  
- LAN-only design  

---

## ⚠️ Disclaimer

For educational and research purposes only.
