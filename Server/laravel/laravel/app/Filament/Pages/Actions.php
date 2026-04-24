<?php

namespace App\Filament\Pages;

use App\Models\Client as ClientModel;
use App\Models\ActionLog;
use App\Services\PythonServer;
use BackedEnum;
use Filament\Pages\Page;
use Filament\Notifications\Notification;

class Actions extends Page
{
    protected static BackedEnum|string|null $navigationIcon = 'heroicon-o-bolt';
    protected static ?string $navigationLabel = 'Actions';
    protected static ?string $title = 'Actions';
    protected static ?string $slug = 'actions';

    protected string $view = 'filament.pages.actions';

    // Single action inputs
    public string $client_id = '';
    public string $action = '';
    public string $message = '';
    
    // Advanced action parameters (for modal)
    public ?int $process_id = null;
    public ?string $service_name = null;
    public ?string $service_action = null;
    public ?string $directory_path = null;

    // Client selector helpers
    public string $clientSearch = '';
    public array $clientOptions = [];
    public bool $showClientList = true;

    // Bulk filters
    public string $q = '';
    public string $tag = '';
    public ?string $status = null; // '1' | '2' | '3' | null

    // UI mode: 'single' | 'bulk'
    public string $mode = 'single';

    // Result + recent logs
    public ?array $result = null;
    public array $recent = [];
    public array $onlineClients = [];

    // Control modal state
    public bool $showControlModal = false;
    public string $controlClientId = '';
    public string $controlMessage = '';
    
    // Screenshot state (for get_screenshot action)
    public bool $showScreenshotModal = false;
    public string $screenshotBase64 = ''; // Base64 encoded screenshot
    public int $screenWidth = 1920;
    public int $screenHeight = 1080;
    public ?string $screenshotCommandId = null; // Command ID for polling
    
    // Command result modal state
    public bool $showResultModal = false;
    public string $resultAction = '';
    public string $resultOutput = '';
    public string $resultError = '';
    public bool $resultSuccess = false;
    public ?string $resultCommandId = null;

    public function mount(): void
    {
        $this->loadRecent();
        $this->loadClientOptions();
        $this->loadOnline();

        // Auto-open control modal when query param present (e.g., ?control=PC-01)
        $control = (string) (request()->query('control') ?? '');
        if ($control !== '') {
            $this->openControl($control);
        }
    }

    public function send(): void
    {
        $normalizedAction = $this->normalizeAction((string) $this->action);
        try {
            if ($this->mode === 'bulk') {
                $payload = [
                    'q' => $this->q !== '' ? $this->q : null,
                    'tag' => $this->tag !== '' ? $this->tag : null,
                    'status' => $this->status !== null && $this->status !== '' ? (int) $this->status : null,
                    'action' => $normalizedAction,
                    'message' => (string) $this->message,
                    'source' => 'Admin',
                    'source_user' => (string) (auth()->user()->email ?? auth()->user()->name ?? 'admin'),
                ];
                // Remove nulls to keep payload clean
                $payload = array_filter($payload, static fn($v) => $v !== null && $v !== '');
                $res = app(PythonServer::class)->post('/control/bulk', $payload)->json();
                $this->result = is_array($res) ? $res : ['ok' => false];
                if (($this->result['ok'] ?? false) && in_array($normalizedAction, ['block', 'unblock', 'notify'], true)) {
                    // Fetch targets using the same filters and mirror to DB
                    $params = [];
                    if ($this->q !== '')
                        $params['q'] = $this->q;
                    if ($this->tag !== '')
                        $params['tag'] = $this->tag;
                    // Map UI status (1/2/3) to Python's 'blocked' filter when applicable
                    if ($this->status !== null && $this->status !== '') {
                        $sv = (int) $this->status;
                        if ($sv === 1) {
                            $params['blocked'] = false;
                        } elseif ($sv === 3) {
                            $params['blocked'] = true;
                        }
                        // if 2 (warning), no 'blocked' filter is applied
                    }
                    $rows = app(PythonServer::class)->get('/clients', $params)->json();
                    $targetIds = [];
                    if (is_array($rows)) {
                        foreach ($rows as $r) {
                            if (!empty($r['client_id']))
                                $targetIds[] = (string) $r['client_id'];
                        }
                    }
                    if (!empty($targetIds)) {
                        $newStatus = 1;
                        if ($normalizedAction === 'block') {
                            $newStatus = 3;
                        } elseif ($normalizedAction === 'notify') {
                            $newStatus = 2;
                        }
                        ClientModel::whereIn('client_id', $targetIds)->update([
                            'status' => $newStatus,
                        ]);
                        $this->loadClientOptions();
                    }
                }
            } else {
                $payload = [
                    'client_id' => (string) $this->client_id,
                    'action' => $normalizedAction,
                    'message' => (string) $this->message,
                    'source' => 'Admin',
                    'source_user' => (string) (auth()->user()->email ?? auth()->user()->name ?? 'admin'),
                ];
                
                
                $res = app(PythonServer::class)->post('/control', $payload)->json();
                $this->result = is_array($res) ? $res : ['ok' => false];
                // Mirror to DB: if request succeeded, always mirror; if action is 'unblock',
                // also mirror even when Python returns 404 (client not currently online in STATE).
                if (in_array($normalizedAction, ['block', 'unblock', 'notify'], true)) {
                    if (($this->result['ok'] ?? false) || $normalizedAction === 'unblock') {
                        $newStatus = 1;
                        if ($normalizedAction === 'block') {
                            $newStatus = 3;
                        } elseif ($normalizedAction === 'notify') {
                            $newStatus = 2;
                        }
                        ClientModel::where('client_id', (string) $this->client_id)->update(['status' => $newStatus]);
                        $this->loadClientOptions();
                    }
                }
            }
        } catch (\Throwable $e) {
            // If single + block/unblock/notify and Python 404 (client offline), treat as success in DB
            if ($this->mode !== 'bulk' && in_array($normalizedAction, ['block', 'unblock', 'notify'], true) && (string) $this->client_id !== '') {
                $newStatus = 1;
                if ($normalizedAction === 'block') {
                    $newStatus = 3;
                } elseif ($normalizedAction === 'notify') {
                    $newStatus = 2;
                }
                ClientModel::where('client_id', (string) $this->client_id)->update(['status' => $newStatus]);
                $this->loadClientOptions();
                $this->result = [
                    'ok' => true,
                    'note' => match ($normalizedAction) {
                        'block' => 'Client offline trên Python server, đã chặn trong DB',
                        'notify' => 'Client offline trên Python server, đã set WARNING trong DB',
                        default => 'Client offline trên Python server, đã mở khóa trong DB',
                    },
                ];
            } else {
                $this->result = [
                    'ok' => false,
                    'error' => $e->getMessage(),
                ];
            }
        } finally {
            $this->loadRecent();
            // Notify user about result
            if ($this->result !== null) {
                $ok = (bool) ($this->result['ok'] ?? false);
                $title = $ok ? 'Gửi lệnh thành công' : 'Gửi lệnh thất bại';
                if ($this->mode === 'bulk') {
                    $countInfo = isset($this->result['count']) ? (' (' . (int) $this->result['count'] . ')') : '';
                    $body = $ok
                        ? (sprintf('Action: %s%s', $normalizedAction, $countInfo))
                        : (string) ($this->result['error'] ?? 'Đã xảy ra lỗi');
                } else {
                    $body = $ok
                        ? (sprintf('Client: %s • Action: %s', (string) $this->client_id, $normalizedAction))
                        : (string) ($this->result['error'] ?? 'Đã xảy ra lỗi');
                }
                $note = Notification::make()
                    ->title($title)
                    ->body($body);
                $ok ? $note->success() : $note->danger();
                $note->send();
            }
        }
    }

    public function loadOnline(): void
    {
        try {
            // Fetch all clients known by Python server
            $rows = app(PythonServer::class)->get('/clients', [])->json();
            $rows = is_array($rows) ? $rows : [];
            // Optionally merge DB online flag if present
            $ids = [];
            foreach ($rows as $r) {
                if (!empty($r['client_id']))
                    $ids[] = (string) $r['client_id'];
            }
            if (!empty($ids)) {
                $db = ClientModel::whereIn('client_id', $ids)
                    ->get(['client_id', 'ip', 'online', 'tags'])
                    ->keyBy('client_id');
                foreach ($rows as $i => $r) {
                    $cid = (string) ($r['client_id'] ?? '');
                    if ($cid === '') {
                        continue;
                    }
                    
                    // Merge data from DB if exists
                    if (isset($db[$cid])) {
                        // Merge online flag
                        if (isset($db[$cid]->online)) {
                            $rows[$i]['online'] = (bool) $db[$cid]->online;
                        }
                        // Merge IP from DB if Python doesn't have it or DB has better IP
                        if (empty($rows[$i]['ip'] ?? '') && !empty($db[$cid]->ip)) {
                            $rows[$i]['ip'] = (string) $db[$cid]->ip;
                        }
                        // Merge tags from DB when Python row lacks them
                        $dbTags = (array) ($db[$cid]->tags ?? []);
                        if (!empty($dbTags) && (!isset($rows[$i]['tags']) || empty($rows[$i]['tags']))) {
                            $rows[$i]['tags'] = array_values(array_filter($dbTags, static fn($t) => (string) $t !== ''));
                        }
                    }
                }
            }
            // Include DB-only clients marked online=1 even if not present in Python
            $existing = [];
            foreach ($rows as $r) {
                if (!empty($r['client_id']))
                    $existing[(string) $r['client_id']] = true;
            }
            $dbOnline = ClientModel::where('online', true)
                ->get(['client_id', 'ip', 'online', 'tags'])
                ->toArray();
            foreach ($dbOnline as $r) {
                $cid = (string) ($r['client_id'] ?? '');
                if ($cid === '' || isset($existing[$cid]))
                    continue;
                $rows[] = [
                    'client_id' => $cid,
                    'ip' => (string) ($r['ip'] ?? ''),
                    'online' => true,
                    'tags' => (array) ($r['tags'] ?? []),
                ];
            }
            // Only keep rows with online true if field exists; otherwise show all returned (treated as online)
            $filtered = [];
            foreach ($rows as $r) {
                if (!isset($r['online']) || $r['online'] === true) {
                    $filtered[] = $r;
                }
            }
            $this->onlineClients = $filtered;
        } catch (\Throwable $e) {
            $this->onlineClients = [];
        }
    }

    public function quick(string $action, string $clientId): void
    {
        $this->client_id = $clientId;
        $this->action = $action;
        $this->message = '';
        $this->mode = 'single';
        $this->send();
    }

    public function pick(string $clientId): void
    {
        $this->client_id = $clientId;
        $this->mode = 'single';
    }

    public function openControl(string $clientId): void
    {
        $this->controlClientId = $clientId;
        $this->client_id = $clientId;
        $this->controlMessage = '';
        $this->showControlModal = true;
    }

    public function closeControl(): void
    {
        $this->showControlModal = false;
        $this->showScreenshotModal = false;
        $this->screenshotBase64 = '';
        $this->screenshotCommandId = null;
        $this->closeResultModal();
    }
    
    public function closeScreenshotModal(): void
    {
        $this->showScreenshotModal = false;
        $this->screenshotBase64 = '';
        $this->screenshotCommandId = null;
    }
    
    public function fetchScreenshot(): void
    {
        // Use command_id if available, otherwise get from controlClientId
        $commandId = $this->screenshotCommandId;
        $target = $this->controlClientId !== '' ? $this->controlClientId : (string) $this->client_id;
        
        if ($commandId === null && $target !== '') {
            // If no command_id, send new command
            try {
                $payload = [
                    'client_id' => $target,
                    'action' => 'get_screenshot',
                    'source' => 'Admin',
                    'source_user' => (string) (auth()->user()->email ?? auth()->user()->name ?? 'admin'),
                    'quality' => 70,
                    'max_width' => 1920,
                    'max_height' => 1080,
                ];
                $res = app(PythonServer::class)->post('/control', $payload)->json();
                
                if (($res['ok'] ?? false) && isset($res['command_id'])) {
                    $commandId = $res['command_id'];
                    $this->screenshotCommandId = $commandId;
                } else {
                    return;
                }
            } catch (\Throwable $e) {
                return;
            }
        }
        
        if ($commandId === null) {
            return;
        }
        
        try {
            // Poll for result
            $resultRes = app(PythonServer::class)->get("/command/result/{$commandId}")->json();
            
            if (($resultRes['ok'] ?? false) && isset($resultRes['result'])) {
                $result = $resultRes['result'];
                if (($result['success'] ?? false) && isset($result['output'])) {
                    $this->screenshotBase64 = (string) $result['output'];
                    if (isset($result['metadata']['screen_width'])) {
                        $this->screenWidth = (int) $result['metadata']['screen_width'];
                    }
                    if (isset($result['metadata']['screen_height'])) {
                        $this->screenHeight = (int) $result['metadata']['screen_height'];
                    }
                    return;
                }
            }
        } catch (\Throwable $e) {
            // Don't show error notification on every refresh
        }
    }
    
    public function pollCommandResult(string $commandId, string $action): void
    {
        // Store command ID and action for polling
        $this->resultCommandId = $commandId;
        $this->resultAction = $action;
        $this->showResultModal = true;
        // Start polling immediately
        $this->fetchCommandResult();
    }
    
    public function fetchCommandResult(): void
    {
        if (!$this->resultCommandId) {
            return;
        }
        
        try {
            $resultRes = app(PythonServer::class)->get("/command/result/{$this->resultCommandId}")->json();
            
            if (($resultRes['ok'] ?? false) && isset($resultRes['result'])) {
                $result = $resultRes['result'];
                $this->resultSuccess = (bool) ($result['success'] ?? false);
                $this->resultOutput = (string) ($result['output'] ?? '');
                $this->resultError = (string) ($result['error'] ?? '');
                
                // Determine if this is a data-returning action
                $dataReturningActions = ['list_processes', 'list_connections', 'list_files', 'get_system_info'];
                $isDataReturning = in_array($this->resultAction, $dataReturningActions, true);
                
                // For data-returning actions, keep modal open to show full result
                // For simple actions, show notification and close modal if not already open
                if (!$isDataReturning && !$this->showResultModal) {
                    // Simple action - just show notification
                    if ($this->resultSuccess) {
                        $outputPreview = $this->resultOutput ? (strlen($this->resultOutput) > 100 ? substr($this->resultOutput, 0, 100) . '...' : $this->resultOutput) : 'Thành công';
                        Notification::make()
                            ->title(ucfirst(str_replace('_', ' ', $this->resultAction)) . ' thành công')
                            ->body($outputPreview)
                            ->success()
                            ->send();
                    } else {
                        Notification::make()
                            ->title(ucfirst(str_replace('_', ' ', $this->resultAction)) . ' thất bại')
                            ->body($this->resultError ?: 'Unknown error')
                            ->danger()
                            ->send();
                    }
                    // Clear result data after showing notification
                    $this->resultCommandId = null;
                    $this->resultAction = '';
                    $this->resultOutput = '';
                    $this->resultError = '';
                } else if ($isDataReturning && !$this->showResultModal) {
                    // Data-returning action - open modal to show full result
                    $this->showResultModal = true;
                }
                // If modal is already open, result will be displayed there
            }
        } catch (\Throwable $e) {
            // If result not ready yet, keep polling (don't show error)
            // Only show error if we've been polling for a while
            if (strpos($e->getMessage(), '404') !== false || strpos($e->getMessage(), 'not found') !== false) {
                // Result not ready yet, will keep polling
                return;
            }
            $this->resultError = 'Lỗi khi lấy kết quả: ' . $e->getMessage();
        }
    }
    
    public function closeResultModal(): void
    {
        $this->showResultModal = false;
        $this->resultCommandId = null;
        $this->resultAction = '';
        $this->resultOutput = '';
        $this->resultError = '';
        $this->resultSuccess = false;
    }
    
    public function pollScreenshot(string $commandId): void
    {
        // Separate method for polling - called from frontend via wire:poll
        try {
            $resultRes = app(PythonServer::class)->get("/command/result/{$commandId}")->json();
            
            if (($resultRes['ok'] ?? false) && isset($resultRes['result'])) {
                $result = $resultRes['result'];
                if (($result['success'] ?? false) && isset($result['output'])) {
                    $this->screenshotBase64 = (string) $result['output'];
                    if (isset($result['metadata']['screen_width'])) {
                        $this->screenWidth = (int) $result['metadata']['screen_width'];
                    }
                    if (isset($result['metadata']['screen_height'])) {
                        $this->screenHeight = (int) $result['metadata']['screen_height'];
                    }
                }
            }
        } catch (\Throwable $e) {
            // Silent fail
        }
    }
    
    // sendMouseClick removed - mouse control feature disabled

    public function doControl(string $action): void
    {
        $target = $this->controlClientId !== '' ? $this->controlClientId : (string) $this->client_id;
        if ($target === '') {
            Notification::make()->title('Chưa chọn client')->warning()->send();
            return;
        }

        // bổ sung request_control để gửi yêu cầu điều khiển chủ động
        $supported = [
            'shutdown', 'restart', 'block', 'unblock', 'notify', 
            'request_control', 'request_metrics', 'get_screenshot',
            'disable_network', 'enable_network', 'list_processes', 
            'kill_process', 'list_connections', 'list_files', 
            'control_service', 'get_system_info'
        ];
        if (!in_array($action, $supported, true)) {
            Notification::make()
                ->title('Chưa hỗ trợ')
                ->body(ucfirst($action) . ' chưa được hỗ trợ')
                ->warning()
                ->send();
            return;
        }
        
        // Handle get_screenshot specially - open modal and fetch screenshot
        if ($action === 'get_screenshot') {
            $this->controlClientId = $target;
            $this->showScreenshotModal = true;
            $this->screenshotBase64 = '';
            $this->screenshotCommandId = null;
            // Send command and get command_id
            try {
                $payload = [
                    'client_id' => $target,
                    'action' => 'get_screenshot',
                    'source' => 'Admin',
                    'source_user' => (string) (auth()->user()->email ?? auth()->user()->name ?? 'admin'),
                    'quality' => 70,
                    'max_width' => 1920,
                    'max_height' => 1080,
                ];
                $res = app(PythonServer::class)->post('/control', $payload)->json();
                if (($res['ok'] ?? false) && isset($res['command_id'])) {
                    $this->screenshotCommandId = $res['command_id'];
                    // Start polling immediately
                    $this->fetchScreenshot();
                }
            } catch (\Throwable $e) {
                // Silent fail
            }
            return;
        }
        
        // For actions that return data (list_processes, list_connections, etc.), 
        // send command directly and poll for result
        $dataReturningActions = ['list_processes', 'list_connections', 'list_files', 'get_system_info'];
        // For simple actions (disable_network, enable_network, etc.), just send and show notification
        $simpleActions = ['disable_network', 'enable_network', 'kill_process', 'control_service'];
        
        if (in_array($action, $dataReturningActions, true)) {
            try {
                $payload = [
                    'client_id' => $target,
                    'action' => $action,
                    'source' => 'Admin',
                    'source_user' => (string) (auth()->user()->email ?? auth()->user()->name ?? 'admin'),
                ];
                // Add special parameters if needed
                if ($action === 'list_files' && !empty($this->directory_path)) {
                    $payload['directory_path'] = $this->directory_path;
                }
                
                $res = app(PythonServer::class)->post('/control', $payload)->json();
                if (($res['ok'] ?? false) && isset($res['command_id'])) {
                    $commandId = $res['command_id'];
                    // Poll for result after a short delay
                    $this->pollCommandResult($commandId, $action);
                } else {
                    Notification::make()
                        ->title('Gửi lệnh thất bại')
                        ->body('Không thể gửi lệnh đến server')
                        ->danger()
                        ->send();
                }
            } catch (\Throwable $e) {
                Notification::make()
                    ->title('Lỗi')
                    ->body('Lỗi khi gửi lệnh: ' . $e->getMessage())
                    ->danger()
                    ->send();
            }
            $this->showControlModal = false;
            return;
        } elseif (in_array($action, $simpleActions, true)) {
            // For simple actions, send command and show notification when result arrives
            try {
                $payload = [
                    'client_id' => $target,
                    'action' => $action,
                    'source' => 'Admin',
                    'source_user' => (string) (auth()->user()->email ?? auth()->user()->name ?? 'admin'),
                ];
                // Add special parameters if needed
                if ($action === 'kill_process' && !empty($this->process_id)) {
                    $payload['process_id'] = (int) $this->process_id;
                }
                if ($action === 'control_service') {
                    if (!empty($this->service_name)) {
                        $payload['service_name'] = $this->service_name;
                    }
                    if (!empty($this->service_action)) {
                        $payload['service_action'] = $this->service_action;
                    }
                }
                
                $res = app(PythonServer::class)->post('/control', $payload)->json();
                if (($res['ok'] ?? false) && isset($res['command_id'])) {
                    // Store command_id to poll result later
                    $this->resultCommandId = $res['command_id'];
                    $this->resultAction = $action;
                    // Poll result after short delay
                    $this->fetchCommandResult();
                    Notification::make()
                        ->title('Đã gửi lệnh')
                        ->body("Lệnh {$action} đã được gửi, đang chờ kết quả...")
                        ->info()
                        ->send();
                } else {
                    Notification::make()
                        ->title('Gửi lệnh thất bại')
                        ->body('Không thể gửi lệnh đến server')
                        ->danger()
                        ->send();
                }
            } catch (\Throwable $e) {
                Notification::make()
                    ->title('Lỗi')
                    ->body('Lỗi khi gửi lệnh: ' . $e->getMessage())
                    ->danger()
                    ->send();
            }
            $this->showControlModal = false;
            return;
        }
        
        // Prepare and send single action, preserving message for notify
        $this->client_id = $target;
        $this->action = $action;
        $this->message = $action === 'notify' ? (string) $this->controlMessage : '';
        $this->mode = 'single';
        $this->send();
        $this->showControlModal = false;
    }

    private function normalizeAction(string $action): string
    {
        $a = strtolower(trim($action));
        return match ($a) {
            '1', 'block' => 'block',
            '0', 'unblock' => 'unblock',
            // Python server does not accept 'warn' as an action. Map UI 'warning' to 'notify'.
            '2', 'warn', 'warning' => 'notify',
            '3', 'notify', 'notification' => 'notify',
            // map 'control' trên UI về 'request_control' để client bật popup Confirm
            'control', 'request_control' => 'request_control',
            default => $a,
        };
    }

    public function loadRecent(): void
    {
        $this->recent = ActionLog::query()
            ->orderByDesc('ts')
            ->limit(20)
            ->get(['ts', 'source', 'action', 'client_id', 'reason'])
            ->toArray();
    }

    public function updatedClientSearch(): void
    {
        $this->loadClientOptions();
    }

    protected function loadClientOptions(): void
    {
        $q = trim($this->clientSearch);
        $query = ClientModel::query();
        if ($q !== '') {
            $query->where(function ($x) use ($q) {
                $x->where('client_id', 'like', "%{$q}%")
                    ->orWhere('ip', 'like', "%{$q}%")
                    ->orWhere('note', 'like', "%{$q}%");
            });
        }
        $rows = $query
            ->orderByDesc('last_seen_ts')
            ->limit(50)
            ->get(['client_id', 'ip', 'status'])
            ->toArray();

        $options = [];
        foreach ($rows as $r) {
            $id = (string) ($r['client_id'] ?? '');
            if ($id === '')
                continue;
            $ip = (string) ($r['ip'] ?? '');
            $status = (int) ($r['status'] ?? 1);
            $label = $id;
            if ($ip !== '')
                $label .= " ({$ip})";
            if ($status === 3) {
                $label .= " • BLOCKED";
            } elseif ($status === 2) {
                $label .= " • WARNING";
            }
            $options[] = ['id' => $id, 'label' => $label];
        }
        $this->clientOptions = $options;
    }
}


