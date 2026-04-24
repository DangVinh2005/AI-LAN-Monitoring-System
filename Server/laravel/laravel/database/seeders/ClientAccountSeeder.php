<?php

namespace Database\Seeders;

use App\Models\Client;
use App\Models\ClientAccount;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\Hash;

class ClientAccountSeeder extends Seeder
{
    public function run(): void
    {
        $clients = Client::query()->get();

        foreach ($clients as $client) {
            $existing = ClientAccount::query()->where('client_id', $client->id)->first();
            if ($existing) {
                continue;
            }

            $emailLocalPart = strtolower(preg_replace('/[^a-z0-9]+/i', '-', (string) $client->client_id));
            if ($emailLocalPart === '' || $emailLocalPart === '-') {
                $emailLocalPart = 'client-' . $client->id;
            }

            ClientAccount::create([
                'client_id' => $client->id,
                'email' => $emailLocalPart . '@client.local',
                'password' => Hash::make('changeme123'),
                'email_verified_at' => now(),
            ]);
        }
    }
}


