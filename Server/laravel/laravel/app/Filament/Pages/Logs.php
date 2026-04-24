<?php

namespace App\Filament\Pages;

use App\Services\PythonServer;
use BackedEnum;
use Filament\Pages\Page;

class Logs extends Page
{
    protected static BackedEnum|string|null $navigationIcon = 'heroicon-o-queue-list';
    protected static ?string $navigationLabel = 'Logs';
    protected static ?string $title = 'Logs';
    protected static ?string $slug = 'logs';

    protected string $view = 'filament.pages.logs';

    public int $limit = 100;
    public ?float $since_ts = null;
    public array $items = [];

    public function mount(): void
    {
        $this->load();
    }

    public function load(): void
    {
        $params = ['limit' => $this->limit];
        if ($this->since_ts !== null && $this->since_ts !== 0.0) {
            $params['since_ts'] = (float) $this->since_ts;
        }
        $res = app(PythonServer::class)->get('/logs', $params)->json();
        $this->items = is_array($res) ? $res : [];
    }
}


