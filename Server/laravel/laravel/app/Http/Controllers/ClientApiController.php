<?php

namespace App\Http\Controllers;

use App\Models\Client;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Log;

class ClientApiController extends Controller
{
    /**
     * Return client profile from database by client_id.
     * Requires auth:sanctum (ClientAccount token).
     */
    public function profile(Request $request, string $client_id)
    {
        try {
            $client = Client::where('client_id', $client_id)->first();
            if (!$client) {
                // Client not found - create basic record (first time access)
                $client = Client::create([
                    'client_id' => $client_id,
                    'ip' => $request->ip(),
                    'status' => 1, // allow
                    'online' => false,
                    'last_seen_ts' => microtime(true),
                ]);
            }

            $account = $client->account()->first();

            return response()->json([
                'client_id' => $client->client_id,
                'ip' => $client->ip,
                'status' => (int) ($client->status ?? 1), // 1=allow, 2=warn, 3=block
                'online' => (bool) ($client->online ?? false),
                'tags' => (array) ($client->tags ?? []),
                'note' => (string) ($client->note ?? ''),
                'last_seen_ts' => (float) ($client->last_seen_ts ?? 0.0),
                'account' => $account ? [
                    'id' => $account->id,
                    'email' => $account->email,
                    'email_verified_at' => $account->email_verified_at,
                ] : null,
            ]);
        } catch (\Throwable $e) {
            try {
                Log::error('client_profile_error', ['error' => $e->getMessage(), 'client_id' => $client_id]);
            } catch (\Throwable $e2) {
            }
            return response()->json(['message' => 'Server error'], 500);
        }
    }

    /**
     * Update online flag (and last_seen_ts) for client by client_id.
     * Body: { online: bool }
     * Requires auth:sanctum.
     */
    public function updateOnline(Request $request, string $client_id)
    {
        try {
            $validated = $request->validate([
                'online' => ['required', 'boolean'],
            ]);
            $client = Client::where('client_id', $client_id)->first();
            if (!$client) {
                // Client not found - create it (first time login from agent)
                $client = Client::create([
                    'client_id' => $client_id,
                    'ip' => $request->input('ip', $request->ip()),
                    'online' => (bool) $validated['online'],
                    'last_seen_ts' => microtime(true),
                ]);
                return response()->json(['ok' => true, 'created' => true]);
            }
            $client->online = (bool) $validated['online'];
            $client->last_seen_ts = microtime(true);
            // Optionally update IP if provided
            $ip = (string) $request->input('ip', '');
            if ($ip !== '') {
                $client->ip = $ip;
            }
            $client->save();
            return response()->json(['ok' => true]);
        } catch (\Illuminate\Validation\ValidationException $ve) {
            return response()->json([
                'message' => 'Validation failed',
                'errors' => $ve->errors(),
            ], 422);
        } catch (\Throwable $e) {
            try {
                Log::error('client_update_online_error', ['error' => $e->getMessage(), 'client_id' => $client_id]);
            } catch (\Throwable $e2) {
            }
            return response()->json(['message' => 'Server error'], 500);
        }
    }

    /**
     * Update client_id (rename client)
     * Body: { new_client_id: string }
     * Requires auth:sanctum.
     */
    public function updateClientId(Request $request, string $client_id)
    {
        try {
            $validated = $request->validate([
                'new_client_id' => ['required', 'string', 'min:3', 'max:255'],
            ]);
            
            $new_client_id = trim($validated['new_client_id']);
            
            // Find current client
            $client = Client::where('client_id', $client_id)->first();
            if (!$client) {
                return response()->json(['message' => 'Client not found'], 404);
            }
            
            // Check if new client_id already exists
            $existing = Client::where('client_id', $new_client_id)->first();
            if ($existing && $existing->id !== $client->id) {
                return response()->json([
                    'message' => 'Client ID already exists',
                    'error' => 'Another client with this ID already exists',
                ], 409); // Conflict
            }
            
            // Update client_id
            $old_client_id = $client->client_id;
            $client->client_id = $new_client_id;
            $client->save();
            
            // Also update in Python server STATE if possible
            try {
                $py = app(\App\Services\PythonServer::class);
                // Rename client in Python STATE (preserves all data)
                $py->patch("/clients/" . urlencode($old_client_id) . "/rename?new_client_id=" . urlencode($new_client_id));
            } catch (\Throwable $e) {
                // Best effort - Python server update may fail, but DB update succeeded
                \Log::warning('python_server_client_id_update_failed', [
                    'old_id' => $old_client_id,
                    'new_id' => $new_client_id,
                    'error' => $e->getMessage(),
                ]);
            }
            
            return response()->json([
                'ok' => true,
                'message' => 'Client ID updated successfully',
                'old_client_id' => $old_client_id,
                'new_client_id' => $new_client_id,
                'client' => [
                    'client_id' => $client->client_id,
                    'ip' => $client->ip,
                    'tags' => $client->tags ?? [],
                    'note' => $client->note ?? '',
                    'online' => (bool) ($client->online ?? false),
                    'status' => (int) ($client->status ?? 1),
                ],
            ]);
        } catch (\Illuminate\Validation\ValidationException $ve) {
            return response()->json([
                'message' => 'Validation failed',
                'errors' => $ve->errors(),
            ], 422);
        } catch (\Throwable $e) {
            try {
                Log::error('client_update_id_error', ['error' => $e->getMessage(), 'client_id' => $client_id]);
            } catch (\Throwable $e2) {
            }
            return response()->json(['message' => 'Server error: ' . $e->getMessage()], 500);
        }
    }

    /**
     * Update client profile (tags, note, ip, etc.)
     * Body: { tags?: array, note?: string, ip?: string }
     * Requires auth:sanctum.
     */
    public function updateProfile(Request $request, string $client_id)
    {
        try {
            $validated = $request->validate([
                'tags' => ['sometimes', 'array'],
                'note' => ['sometimes', 'string', 'nullable'],
                'ip' => ['sometimes', 'string', 'nullable'],
            ]);
            
            $client = Client::where('client_id', $client_id)->first();
            if (!$client) {
                // Client not found - create it (similar to profile endpoint)
                // This allows clients to change their ID and create new record
                $client = Client::create([
                    'client_id' => $client_id,
                    'ip' => $request->input('ip', $request->ip()),
                    'status' => 1, // allow
                    'online' => false,
                    'last_seen_ts' => microtime(true),
                ]);
            }

            if (isset($validated['tags'])) {
                $client->tags = $validated['tags'];
            }
            if (isset($validated['note'])) {
                $client->note = $validated['note'];
            }
            if (isset($validated['ip'])) {
                $client->ip = $validated['ip'];
            }
            
            $client->save();

            return response()->json([
                'ok' => true,
                'client' => [
                    'client_id' => $client->client_id,
                    'ip' => $client->ip,
                    'tags' => $client->tags ?? [],
                    'note' => $client->note ?? '',
                    'online' => (bool) ($client->online ?? false),
                    'status' => (int) ($client->status ?? 1),
                ],
            ]);
        } catch (\Illuminate\Validation\ValidationException $ve) {
            return response()->json([
                'message' => 'Validation failed',
                'errors' => $ve->errors(),
            ], 422);
        } catch (\Throwable $e) {
            try {
                Log::error('client_update_profile_error', ['error' => $e->getMessage(), 'client_id' => $client_id]);
            } catch (\Throwable $e2) {
            }
            return response()->json(['message' => 'Server error'], 500);
        }
    }
}


