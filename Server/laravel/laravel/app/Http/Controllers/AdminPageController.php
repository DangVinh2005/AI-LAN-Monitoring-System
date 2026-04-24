<?php

namespace App\Http\Controllers;

use App\Services\PythonServer;
use Illuminate\Http\Request;

class AdminPageController extends Controller
{
    public function __construct(protected PythonServer $py)
    {
    }

    public function dashboard()
    {
        $stats = $this->py->get('/stats')->json();
        return view('admin.dashboard', compact('stats'));
    }

    public function clients(Request $request)
    {
        $params = $request->only(['q', 'tag', 'blocked']);
        $clients = $this->py->get('/clients', $params)->json();
        return view('admin.clients.index', compact('clients', 'params'));
    }

    public function clientShow(string $id)
    {
        $client = $this->py->get('/clients/' . urlencode($id))->json();
        $history = $this->py->get('/clients/' . urlencode($id) . '/history', ['limit' => 50])->json();
        $queue = $this->py->get('/clients/' . urlencode($id) . '/queue')->json();
        return view('admin.clients.show', compact('client', 'history', 'queue'));
    }

    public function logs(Request $request)
    {
        $items = $this->py->get('/logs', $request->only(['limit', 'since_ts']))->json();
        return view('admin.logs', compact('items'));
    }

    public function patterns()
    {
        $data = $this->py->get('/patterns')->json();
        return view('admin.patterns', ['patterns' => $data['patterns'] ?? []]);
    }

    public function ai()
    {
        $health = $this->py->get('/ai/health')->json();
        return view('admin.ai', compact('health'));
    }

    public function aiTest(Request $request)
    {
        $payload = $request->only(['client_id', 'cpu', 'network_out', 'connections_per_min']);
        // cast numbers
        if (isset($payload['cpu']))
            $payload['cpu'] = floatval($payload['cpu']);
        if (isset($payload['network_out']))
            $payload['network_out'] = floatval($payload['network_out']);
        if (isset($payload['connections_per_min']))
            $payload['connections_per_min'] = intval($payload['connections_per_min']);
        $payload['history'] = [];
        $result = $this->py->post('/ai/test', $payload)->json();
        $health = $this->py->get('/ai/health')->json();
        return view('admin.ai', ['health' => $health, 'result' => $result['result'] ?? null, 'input' => $payload]);
    }
}
