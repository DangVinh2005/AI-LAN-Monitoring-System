<x-filament::page>
    <div class="bg-white dark:bg-gray-800 shadow rounded-lg p-5">
        <form wire:submit.prevent="save" class="space-y-4">
            <label class="block">
                <span class="text-sm text-gray-700 dark:text-gray-200">Patterns JSON</span>
                <textarea wire:model.defer="patternsJson" rows="16" class="mt-1 w-full border border-gray-300 dark:border-gray-700 rounded-md px-3 py-2 bg-white dark:bg-gray-900"></textarea>
            </label>
            <button type="submit" class="inline-flex items-center rounded-md bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 text-sm">Lưu</button>
        </form>
    </div>
</x-filament::page>


