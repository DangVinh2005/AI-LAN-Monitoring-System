<?php

namespace Database\Seeders;

use App\Models\Client;
use Illuminate\Database\Seeder;

class ClientSeeder extends Seeder
{
    public function run(): void
    {
        $now = microtime(true);

        $rows = [
            [
                'client_id' => 'PC-01',
                'ip' => '10.0.0.1',
                'tags' => ['lab', 'demo'],
                'note' => 'Sample client 1',
                'blocked' => false,
                'meta' => ['os' => 'Windows'],
                'last_seen_ts' => $now,
            ],
            [
                'client_id' => 'PC-02',
                'ip' => '10.0.0.2',
                'tags' => ['lab'],
                'note' => 'Sample client 2',
                'blocked' => false,
                'meta' => ['os' => 'Windows'],
                'last_seen_ts' => $now,
            ],
            [
                'client_id' => 'PC-03',
                'ip' => '10.0.0.3',
                'tags' => ['demo'],
                'note' => 'Sample client 3',
                'blocked' => true,
                'meta' => ['os' => 'Linux'],
                'last_seen_ts' => $now,
            ],
            [
                'client_id' => 'PC-04',
                'ip' => '10.0.0.4',
                'tags' => [],
                'note' => null,
                'blocked' => false,
                'meta' => ['os' => 'Windows'],
                'last_seen_ts' => $now,
            ],
            [
                'client_id' => 'PC-05',
                'ip' => '10.0.0.5',
                'tags' => ['test'],
                'note' => 'For UI testing',
                'blocked' => false,
                'meta' => ['os' => 'macOS'],
                'last_seen_ts' => $now,
            ],
        ];

        foreach ($rows as $row) {
            Client::updateOrCreate(
                ['client_id' => $row['client_id']],
                $row,
            );
        }
    }
}
