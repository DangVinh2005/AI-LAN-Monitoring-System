<x-filament::page>
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="bg-white dark:bg-gray-800 shadow rounded-lg p-5">
            <div class="text-sm text-gray-500">Clients</div>
            <div class="text-2xl font-semibold">{{ $this->stats['num_clients'] ?? 0 }}</div>
        </div>
        <div class="bg-white dark:bg-gray-800 shadow rounded-lg p-5">
            <div class="text-sm text-gray-500">Blocked</div>
            <div class="text-2xl font-semibold text-red-600">{{ $this->stats['num_blocked'] ?? 0 }}</div>
        </div>
        <div class="bg-white dark:bg-gray-800 shadow rounded-lg p-5">
            <div class="text-sm text-gray-500">Queued Commands</div>
            <div class="text-2xl font-semibold">{{ $this->stats['num_queued_commands'] ?? 0 }}</div>
        </div>
        <div class="bg-white dark:bg-gray-800 shadow rounded-lg p-5">
            <div class="text-sm text-gray-500">Last Log</div>
            <div class="text-2xl font-semibold">{{ $this->stats['last_log_ts'] ?? 0 }}</div>
        </div>
    </div>

    <div class="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div class="bg-white dark:bg-gray-800 shadow rounded-lg p-5">
            <div class="flex items-center justify-between mb-3">
                <div class="text-sm text-gray-500">Server Health</div>
                @if(($this->health['ok'] ?? false))
                    <span class="inline-flex items-center px-2 py-0.5 rounded-full bg-green-100 text-green-700 text-xs">OK</span>
                @else
                    <span class="inline-flex items-center px-2 py-0.5 rounded-full bg-red-100 text-red-700 text-xs">DOWN</span>
                @endif
            </div>
            <div class="text-xs text-gray-500">Timestamp</div>
            <div class="text-sm">{{ $this->health['ts'] ?? '-' }}</div>
        </div>

        <div class="bg-white dark:bg-gray-800 shadow rounded-lg p-5">
            <div class="text-sm text-gray-500 mb-3">Server Config</div>
            <div class="space-y-2 text-sm">
                <div class="flex items-center justify-between">
                    <div class="text-gray-500">Python Server URL</div>
                    <div class="font-mono">{{ $this->server['base_url'] ?? '-' }}</div>
                </div>
                <div class="flex items-center justify-between">
                    <div class="text-gray-500">Admin API Key</div>
                    <div class="font-mono">{{ ($this->server['api_key_set'] ?? false) ? 'SET' : 'NOT SET' }}</div>
                </div>
            </div>
        </div>
    </div>
</x-filament::page>


