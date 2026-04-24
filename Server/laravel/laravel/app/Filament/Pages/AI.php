<?php

namespace App\Filament\Pages;

use App\Services\PythonServer;
use BackedEnum;
use Filament\Pages\Page;
use Filament\Forms\Concerns\InteractsWithForms;
use Filament\Forms\Contracts\HasForms;
use Filament\Forms;
use Filament\Forms\Components\TextInput;

class AI extends Page implements HasForms
{
    use InteractsWithForms;

    protected static BackedEnum|string|null $navigationIcon = 'heroicon-o-cpu-chip';
    protected static ?string $navigationLabel = 'AI';
    protected static ?string $title = 'AI';
    protected static ?string $slug = 'ai';
    protected string $view = 'filament.pages.ai';

    public array $health = [];
    public ?array $result = null;
    public array $data = [
        'client_id' => '',
        'cpu' => 10,
        'network_out' => 50,
        'connections_per_min' => 5,
    ];

    public function mount(): void
    {
        $this->health = app(PythonServer::class)->get('/ai/health')->json();
        $this->form->fill($this->data);
    }

    public function test(): void
    {
        $state = $this->form->getState();
        $payload = [
            'client_id' => (string) ($state['client_id'] ?? ''),
            'cpu' => (float) ($state['cpu'] ?? 0),
            'network_out' => (float) ($state['network_out'] ?? 0),
            'connections_per_min' => (int) ($state['connections_per_min'] ?? 0),
            'history' => [],
        ];

        $res = app(PythonServer::class)->post('/ai/test', $payload)->json();

        $this->result = $res['result'] ?? null;
        $this->health = app(PythonServer::class)->get('/ai/health')->json();
    }

    // ✅ Cú pháp mới của Filament v4
    protected function getFormSchema(): array
    {
        return [
            TextInput::make('client_id')->label('Client ID')->required(),
            TextInput::make('cpu')->label('CPU')->numeric(),
            TextInput::make('network_out')->label('Network Out')->numeric(),
            TextInput::make('connections_per_min')->label('Connections/Min')->numeric(),
        ];
    }

    // ✅ Thêm statePath cho form
    protected function getFormStatePath(): ?string
    {
        return 'data';
    }
}
