<x-filament::page>
	<x-filament::section>
		<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
			<div>
				<div class="text-sm text-gray-500">Clients</div>
				<div class="text-2xl font-semibold">{{ $this->db['num_clients'] ?? 0 }}</div>
			</div>
			<div>
				<div class="text-sm text-gray-500">Blocked</div>
				<div class="text-2xl font-semibold text-red-600">{{ $this->db['num_blocked'] ?? 0 }}</div>
			</div>
			<div>
				<div class="text-sm text-gray-500">Queued Commands</div>
				<div class="text-2xl font-semibold">{{ $this->stats['num_queued_commands'] ?? 0 }}</div>
			</div>
			<div>
				<div class="text-sm text-gray-500">Last Seen (max)</div>
				<div class="text-2xl font-semibold">{{ $this->db['last_seen_ts_max'] ?? 0 }}</div>
			</div>
		</div>
	</x-filament::section>

	<x-filament::section>
		<div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
			<div>
				<div class="flex items-center justify-between mb-3">
					<div class="text-sm text-gray-500">Server Health</div>
					@if(($this->health['ok'] ?? false))
						<x-filament::badge color="success">OK</x-filament::badge>
					@else
						<x-filament::badge color="danger">DOWN</x-filament::badge>
					@endif
				</div>
				<div class="text-xs text-gray-500">Timestamp</div>
				<div class="text-sm">{{ $this->health['ts'] ?? '-' }}</div>
			</div>

			<div>
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
	</x-filament::section>

	<x-filament::section>
		<div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
			<div>
				<div class="text-sm text-gray-500">CPU Usage</div>
				<div class="text-2xl font-semibold">{{ $this->system['cpu_percent'] ?? '-' }}%</div>
			</div>
			<div>
				<div class="text-sm text-gray-500">Memory</div>
				<div class="text-sm">
					Total: {{ number_format(($this->system['memory']['total'] ?? 0) / (1024*1024*1024), 2) }} GB
				</div>
				<div class="text-sm">
					Used: {{ number_format(($this->system['memory']['used'] ?? 0) / (1024*1024*1024), 2) }} GB ({{ $this->system['memory']['percent'] ?? '-' }}%)
				</div>
			</div>
			<div>
				<div class="text-sm text-gray-500">Disk</div>
				<div class="text-sm">
					Total: {{ number_format(($this->system['disk']['total'] ?? 0) / (1024*1024*1024), 2) }} GB
				</div>
				<div class="text-sm">
					Used: {{ number_format(($this->system['disk']['used'] ?? 0) / (1024*1024*1024), 2) }} GB ({{ $this->system['disk']['percent'] ?? '-' }}%)
				</div>
			</div>
		</div>
	</x-filament::section>
</x-filament::page>



