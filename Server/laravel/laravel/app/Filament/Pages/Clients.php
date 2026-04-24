<?php

namespace App\Filament\Pages;

use App\Services\PythonServer;
use App\Models\Client as ClientModel;
use BackedEnum;
use Filament\Pages\Page;
use Illuminate\Support\Facades\Schema;

class Clients extends Page
{
    protected static BackedEnum|string|null $navigationIcon = 'heroicon-o-computer-desktop';
    protected static ?string $navigationLabel = 'Clients';
    protected static ?string $title = 'Clients';
    protected static ?string $slug = 'clients-browser';

    protected string $view = 'filament.pages.clients';

    public string $q = '';
    public string $tag = '';
    public ?string $status = null; // '1' | '2' | '3' | null

    public array $clients = [];

    public function mount(): void
    {
        $this->load();
    }

    public function load(): void
    {
        $params = [];
        if ($this->q !== '')
            $params['q'] = $this->q;
        if ($this->tag !== '')
            $params['tag'] = $this->tag;
        if ($this->status !== null && $this->status !== '')
            $params['status'] = $this->status;
        $res = app(PythonServer::class)->get('/clients', $params)->json();
        $clients = is_array($res) ? $res : [];

        // Merge canonical fields from database so UI reflects authoritative data
        $ids = [];
        foreach ($clients as $row) {
            if (isset($row['client_id'])) {
                $ids[] = (string) $row['client_id'];
            }
        }
        if (!empty($ids)) {
            $cols = ['client_id', 'tags'];
            if (Schema::hasColumn('clients', 'status'))
                $cols[] = 'status';
            if (Schema::hasColumn('clients', 'online'))
                $cols[] = 'online';

            $dbRows = ClientModel::whereIn('client_id', $ids)
                ->get($cols)
                ->keyBy('client_id');
            foreach ($clients as $i => $row) {
                $cid = (string) ($row['client_id'] ?? '');
                if ($cid === '' || !isset($dbRows[$cid]))
                    continue;

                $db = $dbRows[$cid];
                $clients[$i]['tags'] = $db->tags ?? [];
                // Mirror status/online fields
                if (isset($db->status))
                    $clients[$i]['status'] = (int) $db->status;
                if (isset($db->online))
                    $clients[$i]['online'] = (bool) $db->online;
            }
        }

        $this->clients = $clients;
    }
}


