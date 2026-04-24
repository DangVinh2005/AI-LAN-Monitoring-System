<x-filament::page>
    <div class="bg-white dark:bg-gray-800 shadow rounded-lg p-5">
        <form wire:submit.prevent="load" class="flex flex-col sm:flex-row gap-4 items-end">
            <label class="block">
                <span class="text-sm text-gray-700 dark:text-gray-200">limit</span>
                <input type="number" wire:model.defer="limit" class="mt-1 w-40 border border-gray-300 dark:border-gray-700 rounded-md px-3 py-2 bg-white dark:bg-gray-900" />
            </label>
            <label class="block">
                <span class="text-sm text-gray-700 dark:text-gray-200">since_ts</span>
                <input type="number" step="0.01" wire:model.defer="since_ts" class="mt-1 w-60 border border-gray-300 dark:border-gray-700 rounded-md px-3 py-2 bg-white dark:bg-gray-900" />
            </label>
            <button type="submit" class="inline-flex items-center rounded-md bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 text-sm">Load</button>
        </form>
    </div>

    <div class="mt-6 bg-white dark:bg-gray-800 shadow rounded-lg overflow-hidden">
        <div class="overflow-x-auto">
            <table class="min-w-full text-sm divide-y divide-gray-200 dark:divide-gray-700">
                <thead class="bg-gray-50 dark:bg-gray-900/50">
                    <tr>
                        <th class="px-4 py-2 text-left font-semibold">ts</th>
                        <th class="px-4 py-2 text-left font-semibold">source</th>
                        <th class="px-4 py-2 text-left font-semibold">action</th>
                        <th class="px-4 py-2 text-left font-semibold">client_id</th>
                        <th class="px-4 py-2 text-left font-semibold">reason</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
                    @foreach($this->items as $it)
                        <tr class="hover:bg-gray-50 dark:hover:bg-gray-900/30">
                            <td class="px-4 py-2">{{ $it['ts'] ?? '' }}</td>
                            <td class="px-4 py-2">{{ $it['source'] ?? '' }}</td>
                            <td class="px-4 py-2">{{ $it['action'] ?? '' }}</td>
                            <td class="px-4 py-2">{{ $it['client_id'] ?? '' }}</td>
                            <td class="px-4 py-2">{{ $it['reason'] ?? '' }}</td>
                        </tr>
                    @endforeach
                </tbody>
            </table>
        </div>
    </div>
</x-filament::page>


