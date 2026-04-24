<?php

namespace App\Console\Commands;

use App\Models\ActionLog;
use App\Models\Client;
use App\Services\PythonServer;
use Illuminate\Console\Command;

class SyncPythonData extends Command
{
    protected $signature = 'sync:python {--limit=200}';
    protected $description = 'Sync clients and logs from Python server into DB';

    public function handle(PythonServer $py): int
    {
        $this->info('Syncing clients...');
        $clients = $py->get('/clients')->json() ?? [];
        foreach ($clients as $c) {
            Client::updateOrCreate(
                ['client_id' => $c['client_id']],
                [
                    'ip' => $c['ip'] ?? null,
                    'tags' => $c['tags'] ?? [],
                    'note' => $c['note'] ?? null,
                    'blocked' => (bool) ($c['blocked'] ?? false),
                    'status' => (bool) ($c['blocked'] ?? false) ? 1 : 0,
                    'meta' => $c['meta'] ?? [],
                    'last_seen_ts' => $c['last_seen_ts'] ?? null,
                ]
            );
        }

        $this->info('Syncing logs...');
        $limit = (int) $this->option('limit');
        $logs = $py->get('/logs', ['limit' => $limit])->json() ?? [];
        foreach ($logs as $l) {
            ActionLog::updateOrCreate(
                [
                    'ts' => $l['ts'] ?? 0,
                    'action' => $l['action'] ?? '',
                    'client_id' => $l['client_id'] ?? '',
                ],
                [
                    'source' => $l['source'] ?? 'Admin',
                    'reason' => $l['reason'] ?? null,
                    'source_user' => $l['source_user'] ?? null,
                    'raw' => $l['raw'] ?? [],
                ]
            );
        }

        $this->info('Done.');
        return self::SUCCESS;
    }
}


