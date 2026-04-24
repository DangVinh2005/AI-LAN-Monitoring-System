<x-filament::page>
	<x-filament::section>
		<form wire:submit.prevent="load" class="space-y-4">
			<div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
				<label class="block">
					<span class="text-sm text-gray-700 dark:text-gray-200">Tìm kiếm</span>
					<input type="text" wire:model.defer="q" placeholder="client/ip/tag/note" class="mt-1 w-full border border-gray-300 dark:border-gray-700 rounded-md px-3 py-2 bg-white dark:bg-gray-900" />
				</label>
				<label class="block">
					<span class="text-sm text-gray-700 dark:text-gray-200">Tag</span>
					<input type="text" wire:model.defer="tag" class="mt-1 w-full border border-gray-300 dark:border-gray-700 rounded-md px-3 py-2 bg-white dark:bg-gray-900" />
				</label>
				<label class="block">
					<span class="text-sm text-gray-700 dark:text-gray-200">Trạng thái</span>
					<select wire:model.defer="status" class="mt-1 w-full border border-gray-300 dark:border-gray-700 rounded-md px-3 py-2 bg-white dark:bg-gray-900">
						<option value="">Any</option>
						<option value="1">Allow</option>
						<option value="2">Warning</option>
						<option value="3">Block</option>
					</select>
				</label>
			</div>
			<div class="flex items-center gap-3">
				<x-filament::button type="submit">Lọc</x-filament::button>
				<a target="_blank" href="{{ url('/admin-api/clients?export=true') }}" class="inline-flex items-center rounded-md bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-100 px-4 py-2 text-sm">Export CSV</a>
			</div>
		</form>
	</x-filament::section>

	<x-filament::section>
		<div class="overflow-x-auto">
			<table class="min-w-full text-sm divide-y divide-gray-200 dark:divide-gray-700">
				<thead class="bg-gray-50 dark:bg-gray-900/50">
					<tr>
						<th class="px-4 py-2 text-left font-semibold">Client ID</th>
						<th class="px-4 py-2 text-left font-semibold">IP</th>
						<th class="px-4 py-2 text-left font-semibold">Tags</th>
						<th class="px-4 py-2 text-left font-semibold">Note</th>
						<th class="px-4 py-2 text-left font-semibold">Meta</th>
					<th class="px-4 py-2 text-left font-semibold">Trạng thái</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-gray-200 dark:divide-gray-700">
					@foreach($this->clients as $c)
						<tr class="hover:bg-gray-50 dark:hover:bg-gray-900/30">
							<td class="px-4 py-2">
								<a href="{{ url('/admin/clients?tableSearch='.$c['client_id']) }}" class="text-blue-600 hover:underline">{{ $c['client_id'] }}</a>
							</td>
							<td class="px-4 py-2">{{ $c['ip'] ?? '' }}</td>
							<td class="px-4 py-2">
								@foreach(($c['tags'] ?? []) as $t)
									<x-filament::badge class="mr-1 mb-1">{{ $t }}</x-filament::badge>
								@endforeach
							</td>
							<td class="px-4 py-2 max-w-[24ch] truncate" title="{{ $c['note'] ?? '' }}">{{ $c['note'] ?? '' }}</td>
							<td class="px-4 py-2 max-w-[24ch] truncate" title="{{ is_array($c['meta'] ?? null) ? json_encode($c['meta']) : ($c['meta'] ?? '') }}">
								{{ is_array($c['meta'] ?? null) ? ($c['meta']['os'] ?? json_encode($c['meta'])) : ($c['meta'] ?? '') }}
							</td>
							<td class="px-4 py-2">
							@php
							$status = $c['status'] ?? 1; // 1 allow, 2 warning, 3 block
							$sv = is_numeric($status) ? (int) $status : strtolower((string) $status);
							$show = 'allow';
							if ($sv === 3 || $sv === 'block') $show = 'block';
							elseif ($sv === 2 || $sv === 'warning' || $sv === 'warn') $show = 'warning';
							@endphp
							@if($show==='block')
								<x-filament::badge color="danger">block</x-filament::badge>
							@elseif($show==='warning')
								<x-filament::badge color="warning">warning</x-filament::badge>
							@else
								<x-filament::badge color="success">allow</x-filament::badge>
							@endif
							</td>
						</tr>
					@endforeach
				</tbody>
			</table>
		</div>
	</x-filament::section>
</x-filament::page>


