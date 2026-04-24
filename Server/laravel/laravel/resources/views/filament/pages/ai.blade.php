<x-filament::page>
    <x-filament::section>
        <div>
            <h5>🤖 AI Tester</h5>

            @if($this->health['ok'] ?? false)
                <x-filament::badge color="success">AI Health: OK</x-filament::badge>
            @else
                <x-filament::badge color="danger">AI Health: DOWN</x-filament::badge>
            @endif
        </div>

        {{-- Form kiểm tra --}}
        <form wire:submit.prevent="test">
            {{ $this->form }}

            <div>
                <x-filament::button type="submit">Chạy kiểm tra</x-filament::button>
            </div>
        </form>
    </x-filament::section>

    {{-- Kết quả hiển thị --}}
    @if($this->result)
        <x-filament::section>
            <h6>Kết quả</h6>
            <pre>
{{ json_encode($this->result, JSON_PRETTY_PRINT|JSON_UNESCAPED_UNICODE) }}
            </pre>
        </x-filament::section>
    @endif
</x-filament::page>
