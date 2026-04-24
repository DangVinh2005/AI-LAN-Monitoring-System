Laravel Admin (Filament) Integration Notes

Setup

```bash
composer create-project laravel/laravel admin
cd admin
composer require filament/filament
```

Configure `.env` to point to the Python server. If the FastAPI server runs on Kali, set:

```
PY_SERVER_URL=http://<KALI_IP>:5000
ADMIN_API_KEY=A82CE4A67269D7AC52B1A9D695A49
```

Migrations (outline)

- `clients` table: id, client_id, ip, blocked (bool), last_seen_ts (float), created_at, updated_at
- `action_logs` table: id, ts (float), source (Admin|AI), action, client_id, reason (nullable), source_user (nullable), created_at

Example: Send control to FastAPI

```php
use Illuminate\Support\Facades\Http;

Http::withHeaders(['X-API-Key' => env('ADMIN_API_KEY')])->post(env('PY_SERVER_URL').'/control', [
    'client_id'   => 'PC-03',
    'action'      => 'shutdown',
    'message'     => 'Scheduled maintenance',
    'source'      => 'Admin',
    'source_user' => auth()->user()->name ?? 'admin',
]);
```

Fetch clients and logs

```php
$clients = Http::withHeaders(['X-API-Key' => env('ADMIN_API_KEY')])->get(env('PY_SERVER_URL').'/clients')->json();
$logs    = Http::withHeaders(['X-API-Key' => env('ADMIN_API_KEY')])->get(env('PY_SERVER_URL').'/logs', ['limit' => 200])->json();
```

UI

- Build a Filament table for clients with actions: Shutdown, Restart, Block, Unblock, Notify.
- A Logs page showing timeline grouped by `client_id` with `source` badges.

Quick run (minimal pages included)

```bash
cd laravel/admin
cp .env.example .env
php artisan key:generate
php artisan migrate
php artisan serve
# Pages:
# http://127.0.0.1:8000/clients
# http://127.0.0.1:8000/logs
```
