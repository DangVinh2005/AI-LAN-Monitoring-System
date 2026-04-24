<?php

namespace App\Http\Controllers;

use App\Models\Client;
use App\Models\WebhookEvent;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Log;

class WebhookController extends Controller
{
    public function receive(Request $request)
    {
        $shared = config('services.python_server.webhook_key', env('LARAVEL_WEBHOOK_KEY'));
        $headerKey = $request->header('X-Webhook-Key');
        if ($shared && $shared !== $headerKey) {
            return response()->json(['error' => 'Unauthorized'], 401);
        }

        $type = (string) $request->input('type', 'unknown');
        $data = $request->input('data', []);
        $evt = WebhookEvent::create([
            'type' => $type,
            'data' => $data,
            'received_ts' => microtime(true),
        ]);
        Log::info('Webhook received', ['id' => $evt->id, 'type' => $type]);

        // Mirror status changes to DB for consistency. New semantics: 1=allow, 2=warning, 3=block
        if (in_array($type, ['control', 'control_bulk', 'ai_block', 'ai_warn'], true)) {
            try {
                if ($type === 'ai_block') {
                    $cid = (string) ($data['client_id'] ?? '');
                    if ($cid !== '') {
                        Client::where('client_id', $cid)->update(['status' => 3]);
                    }
                } elseif ($type === 'ai_warn') {
                    $cid = (string) ($data['client_id'] ?? '');
                    if ($cid !== '') {
                        // Directly set status to warning; any escalation to block should be done by backend logic
                        Client::updateOrCreate(
                            ['client_id' => $cid],
                            ['status' => 2]
                        );
                    }
                } elseif ($type === 'control') {
                    $cid = (string) ($data['client_id'] ?? '');
                    $action = (string) ($data['action'] ?? '');
                    if ($cid !== '' && in_array($action, ['block', 'unblock', 'warn', 'allow', 'notify'], true)) {
                        $map = [
                            'allow' => 1,
                            'warn' => 2,
                            'block' => 3,
                            'unblock' => 1,
                            'notify' => 2,
                        ];
                        Client::where('client_id', $cid)->update(['status' => $map[$action] ?? 1]);
                    }
                } elseif ($type === 'control_bulk') {
                    $ids = (array) ($data['client_ids'] ?? []);
                    $action = (string) ($data['action'] ?? '');
                    if (!empty($ids) && in_array($action, ['block', 'unblock', 'warn', 'allow', 'notify'], true)) {
                        $map = [
                            'allow' => 1,
                            'warn' => 2,
                            'block' => 3,
                            'unblock' => 1,
                            'notify' => 2,
                        ];
                        Client::whereIn('client_id', $ids)->update(['status' => $map[$action] ?? 1]);
                    }
                }
            } catch (\Throwable $e) {
                Log::warning('Failed to mirror block state from webhook', ['error' => $e->getMessage()]);
            }
        }

        return response()->json(['ok' => true]);
    }
}
