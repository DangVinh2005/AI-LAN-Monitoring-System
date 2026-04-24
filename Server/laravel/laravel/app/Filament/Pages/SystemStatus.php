<?php

namespace App\Filament\Pages;

use App\Services\PythonServer;
use App\Models\Client;
use BackedEnum;
use Filament\Pages\Page;

class SystemStatus extends Page
{
    protected static BackedEnum|string|null $navigationIcon = 'heroicon-o-cog-8-tooth';
    protected static ?string $navigationLabel = 'System Status';
    protected static ?string $title = 'System Status';
    protected static ?string $slug = 'system-status';

    protected string $view = 'filament.pages.system-status';

    public array $stats = [];
    public array $health = [];
    public array $server = [];
    public array $system = [];
    public array $db = [];

    public function mount(): void
    {
        $this->stats = app(PythonServer::class)->get('/stats')->json() ?? [];
        $this->health = app(PythonServer::class)->get('/health')->json() ?? [];
        $this->server = [
            'base_url' => rtrim(config('services.python_server.base_url', env('PY_SERVER_URL', 'http://localhost:5000')), '/'),
            'api_key_set' => (bool) (config('services.python_server.api_key', env('ADMIN_API_KEY'))),
        ];
        $this->system = app(PythonServer::class)->get('/system')->json() ?? [];

        // Use database counts for clients to reflect canonical state
        $this->db = [
            'num_clients' => (int) Client::count(),
            // New semantics: 3 = block
            'num_blocked' => (int) Client::where('status', 3)->count(),
            'last_seen_ts_max' => (float) (Client::max('last_seen_ts') ?? 0.0),
        ];
    }
}



