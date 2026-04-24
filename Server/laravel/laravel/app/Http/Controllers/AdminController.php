<?php

namespace App\Http\Controllers;

use App\Services\PythonServer;
use Illuminate\Http\Request;

class AdminController extends Controller
{
    public function __construct(protected PythonServer $py)
    {
    }

    public function clients(Request $request)
    {
        $res = $this->py->get('/clients', $request->only(['q', 'tag', 'blocked', 'export']));
        return response($res->body(), $res->status())->withHeaders($res->headers());
    }

    public function clientShow(string $id)
    {
        $res = $this->py->get('/clients/' . urlencode($id));
        return response()->json($res->json());
    }

    public function clientUpdate(Request $request, string $id)
    {
        $res = $this->py->patch('/clients/' . urlencode($id), $request->only(['tags', 'note', 'blocked']));
        return response()->json($res->json());
    }

    public function clientDelete(string $id)
    {
        $res = $this->py->delete('/clients/' . urlencode($id));
        return response()->json($res->json());
    }

    public function clientHistory(Request $request, string $id)
    {
        $res = $this->py->get('/clients/' . urlencode($id) . '/history', $request->only(['limit']));
        return response()->json($res->json());
    }

    public function clientHistoryClear(string $id)
    {
        $res = $this->py->delete('/clients/' . urlencode($id) . '/history');
        return response()->json($res->json());
    }

    public function clientQueue(string $id)
    {
        $res = $this->py->get('/clients/' . urlencode($id) . '/queue');
        return response()->json($res->json());
    }

    public function clientQueueClear(string $id)
    {
        $res = $this->py->delete('/clients/' . urlencode($id) . '/queue');
        return response()->json($res->json());
    }

    public function control(Request $request)
    {
        // Forward all control request fields including new command fields
        $payload = $request->only([
            'client_id', 
            'action', 
            'message', 
            'source', 
            'source_user',
            'command',      // For execute_command
            'file_path',    // For upload_file/download_file
            'file_data',    // For upload_file (base64 encoded)
            'target_path',  // For download_file
            'process_id',   // For kill_process
            'service_name', // For control_service
            'service_action', // For control_service
            'directory_path', // For list_files
        ]);
        $res = $this->py->post('/control', $payload);
        return response()->json($res->json());
    }

    public function controlBulk(Request $request)
    {
        // Forward all bulk control request fields including new command fields
        $payload = $request->only([
            'client_ids', 
            'q', 
            'tag', 
            'blocked', 
            'action', 
            'message', 
            'source', 
            'source_user',
            'command',      // For execute_command
            'file_path',    // For upload_file/download_file
            'file_data',    // For upload_file (base64 encoded)
            'target_path',  // For download_file
            'process_id',   // For kill_process
            'service_name', // For control_service
            'service_action', // For control_service
            'directory_path', // For list_files
        ]);
        $res = $this->py->post('/control/bulk', $payload);
        return response()->json($res->json());
    }

    public function patternsGet()
    {
        $res = $this->py->get('/patterns');
        return response()->json($res->json());
    }

    public function patternsPut(Request $request)
    {
        $res = $this->py->put('/patterns', ['patterns' => $request->input('patterns', [])]);
        return response()->json($res->json());
    }

    public function tagsBulk(Request $request)
    {
        $res = $this->py->post('/clients/tags:bulk', $request->only(['client_ids', 'q', 'tag', 'blocked', 'add', 'remove']));
        return response()->json($res->json());
    }

    public function logs(Request $request)
    {
        $res = $this->py->get('/logs', $request->only(['limit', 'since_ts']));
        return response()->json($res->json());
    }

    public function stats()
    {
        $res = $this->py->get('/stats');
        return response()->json($res->json());
    }

    public function aiHealth()
    {
        $res = $this->py->get('/ai/health');
        return response()->json($res->json());
    }

    public function aiTest(Request $request)
    {
        $res = $this->py->post('/ai/test', $request->all());
        return response()->json($res->json());
    }
}
