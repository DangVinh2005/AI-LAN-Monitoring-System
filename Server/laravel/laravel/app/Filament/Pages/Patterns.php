<?php

namespace App\Filament\Pages;

use App\Services\PythonServer;
use BackedEnum;
use Filament\Notifications\Notification;
use Filament\Pages\Page;

class Patterns extends Page
{
    protected static BackedEnum|string|null $navigationIcon = 'heroicon-o-code-bracket-square';
    protected static ?string $navigationLabel = 'Patterns';
    protected static ?string $title = 'Patterns';
    protected static ?string $slug = 'patterns';

    protected string $view = 'filament.pages.patterns';

    public string $patternsJson = "";

    public function mount(): void
    {
        $data = app(PythonServer::class)->get('/patterns')->json();
        $this->patternsJson = json_encode($data['patterns'] ?? [], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
    }

    public function save(): void
    {
        $decoded = json_decode($this->patternsJson, true);
        if (!is_array($decoded)) {
            Notification::make()
                ->title('JSON không hợp lệ')
                ->danger()
                ->send();
            return;
        }
        app(PythonServer::class)->put('/patterns', ['patterns' => $decoded]);
        Notification::make()
            ->title('Đã lưu patterns')
            ->success()
            ->send();
    }
}


