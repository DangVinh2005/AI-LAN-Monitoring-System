<x-filament::page>
    <style>
        /* Force table borders regardless of Filament/Tailwind resets */
        .table-bordered {
            border-collapse: collapse !important;
            border-spacing: 0 !important;
        }

        .table-bordered,
        .table-bordered th,
        .table-bordered td {
            border: 2px solid #9ca3af !important;
        }

        /* Action modal improvements */
        .action-modal-overlay {
            position: fixed;
            inset: 0;
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
            animation: fadeIn 0.2s ease-out;
        }

        .action-modal-content {
            position: relative;
            background: white;
            color: inherit;
            width: min(100%, 56rem);
            margin: 0 1rem;
            padding: 0;
            border-radius: 0.5rem;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
            animation: slideUp 0.3s ease-out;
            max-height: 90vh;
            overflow-y: auto;
        }

        @media (prefers-color-scheme: dark) {
            .action-modal-content {
                background: #1f2937;
            }
        }

        @keyframes fadeIn {
            from {
                opacity: 0;
            }

            to {
                opacity: 1;
            }
        }

        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }

            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .action-group {
            background: #f9fafb;
            border-radius: 0.5rem;
            padding: 1rem;
            border: 1px solid #e5e7eb;
        }

        @media (prefers-color-scheme: dark) {
            .action-group {
                background: #111827;
                border-color: #374151;
            }
        }

        .action-button-group {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 0.75rem;
        }

        .action-icon {
            display: inline-block;
            width: 1.25rem;
            height: 1.25rem;
            margin-right: 0.5rem;
            vertical-align: middle;
        }
    </style>

    <x-filament::section>
        <div class="flex items-center gap-3">
            <x-filament::button color="gray" wire:click="$set('mode','single')" :disabled="$this->mode === 'single'">
                Gửi lệnh 1 client
            </x-filament::button>
            <x-filament::button color="gray" wire:click="$set('mode','bulk')" :disabled="$this->mode === 'bulk'">
                Gửi lệnh hàng loạt
            </x-filament::button>
        </div>
    </x-filament::section>

    {{-- Control Modal --}}
    @if ($this->showControlModal)
        <div class="action-modal-overlay">
            <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" wire:click="closeControl"></div>
            <div class="action-modal-content">
                {{-- Modal Header --}}
                <div class="relative p-6 border-b flex items-start " style="color:#ffffff">
                    <!-- Nút close X — nằm góc phải -->
                    <x-filament::button icon="heroicon-m-x-mark" color="gray" size="sm" wire:click="closeControl"
                        class="absolute top-2 right-2 !rounded-full text-white">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M6 18L18 6M6 6l12 12">
                            </path>
                        </svg>
                    </x-filament::button>
                    <!-- Phần nội dung -->
                    <div>
                        <h3 class="text-2xl font-bold" style="color:#ffffff">Điều khiển Client</h3>
                        <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
                            Client ID:
                            <span class="font-mono font-semibold" style="color:#ffffff">
                                {{ $this->controlClientId }}
                            </span>
                        </p>
                    </div>
                </div>
                {{-- Modal Body --}}
                <div class="p-6 space-y-6">
                    {{-- Basic Actions --}}
                    <div class="action-group">
                        <h4 class="font-semibold mb-3 flex items-center gap-2" style="color:#ffffff">
                            <svg class="w-2 h-2 text-primary-600 dark:text-primary-400" style="width:16px; height:16px"
                                fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4">
                                </path>
                            </svg>
                            Hành động cơ bản
                        </h4>
                        <div class="action-button-group">
                            <x-filament::button color="danger" wire:click="doControl('shutdown')"
                                class="w-full justify-center" title="Tắt máy client ngay lập tức">
                                <svg class="w-2 h-2 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                        d="M5 13l4 4L19 7"></path>
                                </svg>
                                Shutdown
                            </x-filament::button>
                            <x-filament::button color="warning" wire:click="doControl('restart')"
                                class="w-full justify-center" title="Khởi động lại máy client">
                                <svg class="w-2 h-2 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                        d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15">
                                    </path>
                                </svg>
                                Restart
                            </x-filament::button>
                            <x-filament::button color="gray" wire:click="doControl('block')"
                                class="w-full justify-center" title="Chặn client (DB + server)">
                                <svg class="w-2 h-2 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                        d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636">
                                    </path>
                                </svg>
                                Block
                            </x-filament::button>
                            <x-filament::button color="success" wire:click="doControl('unblock')"
                                class="w-full justify-center" title="Bỏ chặn client">
                                <svg class="w-2 h-2 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                </svg>
                                Unblock
                            </x-filament::button>
                            <x-filament::button color="warning" wire:click="doControl('notify')"
                                class="w-full justify-center" title="Gửi cảnh báo tới client">
                                <svg class="w-2 h-2 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                        d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z">
                                    </path>
                                </svg>
                                Warning
                            </x-filament::button>
                        </div>
                    </div>
                    {{-- Send Message --}}
                    <div class="action-group">
                        <h4 class="font-semibold mb-3 flex items-center gap-2" style="color:#ffffff">
                            <svg class="w-2 h-2 text-primary-600 dark:text-primary-400"
                                style="width:16px; height:16px" fill="none" stroke="currentColor"
                                viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z">
                                </path>
                            </svg>
                            Gửi tin nhắn
                        </h4>
                        <div class="flex items-center gap-3">
							<input type="text" wire:model.defer="controlMessage"
							placeholder="Nhập nội dung tin nhắn..." style="color:#ffffff"
							class="flex-1 
								   border border-gray-300 
								   dark:border-white
								   rounded-lg px-4 py-2.5 
								   bg-white dark:bg-gray-800 
								   focus:ring-2 focus:ring-primary-500 focus:border-transparent 
								   transition-all" />						
                            <x-filament::button color="primary" wire:click="doControl('notify')" class="px-6">
                                <svg class="w-2 h-2 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                        d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
                                </svg>
                                Gửi
                            </x-filament::button>
                        </div>
                    </div>

                    {{-- Advanced Actions --}}
                    <div class="action-group">
                        <h4 class="font-semibold mb-3 flex items-center gap-2" style="color:#ffffff">
                            <svg class="w-2 h-2 text-primary-600 dark:text-primary-400"
                                style="width:16px; height:16px" fill="none" stroke="currentColor"
                                viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                            </svg>
                            Tính năng nâng cao
                        </h4>
                        <div class="space-y-4">
                            {{-- Network Actions --}}
                            <div>
                                <h5 class="text-sm font-medium mb-2 text-gray-300 dark:text-gray-400">Mạng</h5>
                                <div class="action-button-group">
                                    <x-filament::button color="danger" wire:click="doControl('disable_network')"
                                        class="w-full justify-center" title="Tắt mạng của client">
                                        <svg class="w-2 h-2 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                                d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636"></path>
                                        </svg>
                                        Tắt mạng
                                    </x-filament::button>
                                    <x-filament::button color="success" wire:click="doControl('enable_network')"
                                        class="w-full justify-center" title="Bật mạng của client">
                                        <svg class="w-2 h-2 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                        </svg>
                                        Bật mạng
                                    </x-filament::button>
                                    <x-filament::button color="info" wire:click="doControl('list_connections')"
                                        class="w-full justify-center" title="Xem danh sách kết nối mạng">
                                        <svg class="w-2 h-2 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                                d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"></path>
                                        </svg>
                                        Kết nối mạng
                                    </x-filament::button>
                                </div>
                            </div>
                            
                            {{-- Process Actions --}}
                            <div>
                                <h5 class="text-sm font-medium mb-2 text-gray-300 dark:text-gray-400">Process</h5>
                                <div class="action-button-group">
                                    <x-filament::button color="info" wire:click="doControl('list_processes')"
                                        class="w-full justify-center" title="Xem danh sách tất cả processes">
                                        <svg class="w-2 h-2 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
                                        </svg>
                                        Danh sách Process
                                    </x-filament::button>
                                    <x-filament::button color="warning" wire:click="doControl('kill_process')"
                                        class="w-full justify-center" title="Kill một process (cần nhập PID)">
                                        <svg class="w-2 h-2 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                                d="M6 18L18 6M6 6l12 12"></path>
                                        </svg>
                                        Kill Process
                                    </x-filament::button>
                                </div>
                            </div>
                            
                            {{-- System Actions --}}
                            <div>
                                <h5 class="text-sm font-medium mb-2 text-gray-300 dark:text-gray-400">Hệ thống</h5>
                                <div class="action-button-group">
                                    <x-filament::button color="primary" wire:click="doControl('get_screenshot')"
                                        class="w-full justify-center" title="Chụp màn hình của client và hiển thị">
                                        <svg class="w-2 h-2 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                                d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z">
                                            </path>
                                        </svg>
                                        Chụp màn hình
                                    </x-filament::button>
                                    <x-filament::button color="info" wire:click="doControl('get_system_info')"
                                        class="w-full justify-center" title="Xem thông tin hệ thống">
                                        <svg class="w-2 h-2 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                                        </svg>
                                        Thông tin hệ thống
                                    </x-filament::button>
                                    <x-filament::button color="info" wire:click="doControl('list_files')"
                                        class="w-full justify-center" title="Duyệt file system">
                                        <svg class="w-2 h-2 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                                d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"></path>
                                        </svg>
                                        Duyệt File System
                                    </x-filament::button>
                                    <x-filament::button color="warning" wire:click="doControl('control_service')"
                                        class="w-full justify-center" title="Điều khiển system service">
                                        <svg class="w-2 h-2 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                                d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                                        </svg>
                                        Điều khiển Service
                                    </x-filament::button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    @endif

    {{-- Command Result Modal --}}
    @if ($this->showResultModal)
        <div class="action-modal-overlay" wire:click="closeResultModal" style="color: #ffffff;">
            <div class="action-modal-content" style="max-width: 90vw; max-height: 90vh;" wire:click.stop
                 wire:poll.2s="fetchCommandResult">
                <div class="relative p-4 border-b flex items-center justify-between bg-gray-900">
                    <div class="flex items-center gap-4">
                        <h3 class="text-xl font-bold text-white"></h3>
                            Kết quả: {{ ucfirst(str_replace('_', ' ', $this->resultAction)) }} - {{ $this->controlClientId }}
                        </h3>
                        <x-filament::button size="sm" color="gray" wire:click="fetchCommandResult" 
                            class="!text-white" title="Làm mới kết quả">
                            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15">
                                </path>
                            </svg>
                            Làm mới
                        </x-filament::button>
                    </div>
                    <x-filament::button icon="heroicon-m-x-mark" color="gray" size="sm" wire:click="closeResultModal"
                        class="!rounded-full !text-white">
                    </x-filament::button>
                </div>
                <div class="p-4 bg-gray-800 overflow-auto" style="max-height: calc(90vh - 120px);">
                    @if ($this->resultCommandId && !$this->resultOutput && !$this->resultError)
                        <div class="flex items-center justify-center w-full h-96">
                            <div class="text-center">
                                <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
                                <p class="text-white">Đang chờ kết quả từ client...</p>
                                <p class="text-gray-400 text-sm mt-2">Command ID: {{ $this->resultCommandId }}</p>
                            </div>
                        </div>
                    @elseif ($this->resultSuccess)
                        <div class="space-y-4" x-data="{ viewMode: 'table' }">
                            @if ($this->resultError)
                                <div class="bg-yellow-900/50 border border-yellow-600 rounded-lg p-4">
                                    <h4 class="text-yellow-400 font-semibold mb-2">Cảnh báo:</h4>
                                    <pre class="text-yellow-200 text-sm whitespace-pre-wrap">{{ $this->resultError }}</pre>
                                </div>
                            @endif
                            @if ($this->resultOutput)
                                @php
                                    // Try to parse JSON output
                                    $jsonData = null;
                                    $isJson = false;
                                    try {
                                        $jsonData = json_decode($this->resultOutput, true);
                                        $isJson = is_array($jsonData) || is_object($jsonData);
                                    } catch (\Exception $e) {
                                        $isJson = false;
                                    }
                                    
                                    // Determine if this is a list/array result
                                    $isList = $isJson && is_array($jsonData) && isset($jsonData[0]) && is_array($jsonData[0]);
                                @endphp
                                
                                @if ($isList && in_array($this->resultAction, ['list_connections', 'list_processes', 'list_files']))
                                    {{-- Display as table for list results --}}
                                    <div class="bg-gray-900 border border-gray-600 rounded-lg p-4">
                                        <div class="flex items-center justify-between mb-4">
                                            <h4 class="text-green-400 font-semibold">
                                                Kết quả: {{ count($jsonData) }} mục
                                            </h4>
                                            <div class="flex gap-2">
                                                <x-filament::button size="sm" color="gray" 
                                                    x-on:click="viewMode = viewMode === 'table' ? 'json' : 'table'"
                                                    class="!text-white">
                                                    <span x-text="viewMode === 'table' ? 'Xem JSON' : 'Xem Bảng'"></span>
                                                </x-filament::button>
                                            </div>
                                        </div>
                                        
                                        {{-- Table View --}}
                                        <div x-show="viewMode === 'table'" class="overflow-x-auto">
                                            <table class="min-w-full text-sm border-collapse border border-gray-600">
                                                <thead class="bg-gray-800">
                                                    <tr>
                                                        @if ($this->resultAction === 'list_connections')
                                                            <th class="px-4 py-2 text-left text-gray-300 border border-gray-600">PID</th>
                                                            <th class="px-4 py-2 text-left text-gray-300 border border-gray-600">Process</th>
                                                            <th class="px-4 py-2 text-left text-gray-300 border border-gray-600">Local Address</th>
                                                            <th class="px-4 py-2 text-left text-gray-300 border border-gray-600">Remote Address</th>
                                                            <th class="px-4 py-2 text-left text-gray-300 border border-gray-600">Status</th>
                                                            <th class="px-4 py-2 text-left text-gray-300 border border-gray-600">Type</th>
                                                        @elseif ($this->resultAction === 'list_processes')
                                                            <th class="px-4 py-2 text-left text-gray-300 border border-gray-600">PID</th>
                                                            <th class="px-4 py-2 text-left text-gray-300 border border-gray-600">Name</th>
                                                            <th class="px-4 py-2 text-left text-gray-300 border border-gray-600">User</th>
                                                            <th class="px-4 py-2 text-left text-gray-300 border border-gray-600">CPU %</th>
                                                            <th class="px-4 py-2 text-left text-gray-300 border border-gray-600">Memory %</th>
                                                            <th class="px-4 py-2 text-left text-gray-300 border border-gray-600">Command</th>
                                                        @elseif ($this->resultAction === 'list_files')
                                                            <th class="px-4 py-2 text-left text-gray-300 border border-gray-600">Name</th>
                                                            <th class="px-4 py-2 text-left text-gray-300 border border-gray-600">Type</th>
                                                            <th class="px-4 py-2 text-left text-gray-300 border border-gray-600">Size</th>
                                                            <th class="px-4 py-2 text-left text-gray-300 border border-gray-600">Modified</th>
                                                            <th class="px-4 py-2 text-left text-gray-300 border border-gray-600">Permissions</th>
                                                        @endif
                                                    </tr>
                                                </thead>
                                                <tbody class="text-gray-200">
                                                    @foreach (array_slice($jsonData, 0, 500) as $item)
                                                        <tr class="border-b border-gray-600 hover:bg-gray-800/50">
                                                            @if ($this->resultAction === 'list_connections')
                                                                <td class="px-4 py-2 font-mono border border-gray-600">{{ $item['pid'] ?? 'N/A' }}</td>
                                                                <td class="px-4 py-2 border border-gray-600">{{ $item['process_name'] ?? 'N/A' }}</td>
                                                                <td class="px-4 py-2 font-mono text-xs border border-gray-600">{{ $item['laddr'] ?? 'N/A' }}</td>
                                                                <td class="px-4 py-2 font-mono text-xs border border-gray-600">{{ $item['raddr'] ?? 'N/A' }}</td>
                                                                <td class="px-4 py-2 border border-gray-600">
                                                                    <span class="px-2 py-1 rounded text-xs 
                                                                        {{ ($item['status'] ?? '') === 'ESTABLISHED' ? 'bg-green-900/50 text-green-300' : 
                                                                           (($item['status'] ?? '') === 'LISTEN' ? 'bg-blue-900/50 text-blue-300' : 
                                                                           'bg-gray-700 text-gray-300') }}">
                                                                        {{ $item['status'] ?? 'N/A' }}
                                                                    </span>
                                                                </td>
                                                                <td class="px-4 py-2 text-xs border border-gray-600">{{ $item['type'] ?? 'N/A' }}</td>
                                                            @elseif ($this->resultAction === 'list_processes')
                                                                <td class="px-4 py-2 font-mono border border-gray-600">{{ $item['pid'] ?? 'N/A' }}</td>
                                                                <td class="px-4 py-2 font-semibold border border-gray-600">{{ $item['name'] ?? 'N/A' }}</td>
                                                                <td class="px-4 py-2 text-xs border border-gray-600">{{ $item['username'] ?? 'N/A' }}</td>
                                                                <td class="px-4 py-2 border border-gray-600">
                                                                    <span class="px-2 py-1 rounded text-xs 
                                                                        {{ ($item['cpu_percent'] ?? 0) > 50 ? 'bg-red-900/50 text-red-300' : 
                                                                           (($item['cpu_percent'] ?? 0) > 20 ? 'bg-yellow-900/50 text-yellow-300' : 
                                                                           'bg-gray-700 text-gray-300') }}">
                                                                        {{ number_format($item['cpu_percent'] ?? 0, 1) }}%
                                                                    </span>
                                                                </td>
                                                                <td class="px-4 py-2 border border-gray-600">
                                                                    <span class="px-2 py-1 rounded text-xs 
                                                                        {{ ($item['memory_percent'] ?? 0) > 50 ? 'bg-red-900/50 text-red-300' : 
                                                                           (($item['memory_percent'] ?? 0) > 20 ? 'bg-yellow-900/50 text-yellow-300' : 
                                                                           'bg-gray-700 text-gray-300') }}">
                                                                        {{ number_format($item['memory_percent'] ?? 0, 1) }}%
                                                                    </span>
                                                                </td>
                                                                <td class="px-4 py-2 text-xs font-mono truncate max-w-xs border border-gray-600" title="{{ $item['cmdline'] ?? '' }}">
                                                                    {{ Str::limit($item['cmdline'] ?? 'N/A', 50) }}
                                                                </td>
                                                            @elseif ($this->resultAction === 'list_files')
                                                                <td class="px-4 py-2 border border-gray-600">
                                                                    <div class="flex items-center gap-2">
                                                                        @if (($item['type'] ?? '') === 'directory')
                                                                            <svg class="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"></path>
                                                                            </svg>
                                                                        @else
                                                                            <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                                                                            </svg>
                                                                        @endif
                                                                        <span class="font-semibold">{{ $item['name'] ?? 'N/A' }}</span>
                                                                    </div>
                                                                </td>
                                                                <td class="px-4 py-2 border border-gray-600">
                                                                    <span class="px-2 py-1 rounded text-xs 
                                                                        {{ ($item['type'] ?? '') === 'directory' ? 'bg-blue-900/50 text-blue-300' : 'bg-gray-700 text-gray-300' }}">
                                                                        {{ $item['type'] ?? 'N/A' }}
                                                                    </span>
                                                                </td>
                                                                <td class="px-4 py-2 font-mono text-xs border border-gray-600">
                                                                    @if (isset($item['size']) && $item['size'] !== null)
                                                                        {{ $item['size'] > 1024*1024 ? number_format($item['size'] / (1024*1024), 2) . ' MB' : 
                                                                           ($item['size'] > 1024 ? number_format($item['size'] / 1024, 2) . ' KB' : $item['size'] . ' B') }}
                                                                    @else
                                                                        N/A
                                                                    @endif
                                                                </td>
                                                                <td class="px-4 py-2 text-xs border border-gray-600">
                                                                    @if (isset($item['modified']))
                                                                        {{ date('Y-m-d H:i:s', (int)$item['modified']) }}
                                                                    @else
                                                                        N/A
                                                                    @endif
                                                                </td>
                                                                <td class="px-4 py-2 font-mono text-xs border border-gray-600">{{ $item['permissions'] ?? 'N/A' }}</td>
                                                            @endif
                                                        </tr>
                                                    @endforeach
                                                </tbody>
                                            </table>
                                            @if (count($jsonData) > 500)
                                                <div class="mt-4 text-center text-gray-400 text-sm">
                                                    Hiển thị 500/{{ count($jsonData) }} mục đầu tiên
                                                </div>
                                            @endif
                                        </div>
                                        
                                        {{-- JSON View --}}
                                        <div x-show="viewMode === 'json'" class="hidden">
                                            <pre class="text-gray-100 text-xs whitespace-pre-wrap font-mono overflow-x-auto bg-gray-950 p-4 rounded border border-gray-700">{{ json_encode($jsonData, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) }}</pre>
                                        </div>
                                    </div>
                                @elseif ($isJson)
                                    {{-- Formatted JSON for non-list results --}}
                                    <div class="bg-gray-900 border border-gray-600 rounded-lg p-4">
                                        <h4 class="text-green-400 font-semibold mb-2">Kết quả (JSON):</h4>
                                        <pre class="text-gray-100 text-xs whitespace-pre-wrap font-mono overflow-x-auto bg-gray-950 p-4 rounded border border-gray-700">{{ json_encode($jsonData, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) }}</pre>
                                    </div>
                                @else
                                    {{-- Plain text output --}}
                                    <div class="bg-gray-900 border border-gray-600 rounded-lg p-4">
                                        <h4 class="text-green-400 font-semibold mb-2">Kết quả:</h4>
                                        <pre class="text-gray-100 text-sm whitespace-pre-wrap font-mono overflow-x-auto">{{ $this->resultOutput }}</pre>
                                    </div>
                                @endif
                            @else
                                <div class="bg-green-900/50 border border-green-600 rounded-lg p-4">
                                    <p class="text-green-200">Command đã thực thi thành công (không có output)</p>
                                </div>
                            @endif
                        </div>
                    @else
                        <div class="bg-red-900/50 border border-red-600 rounded-lg p-4">
                            <h4 class="text-red-400 font-semibold mb-2">Lỗi:</h4>
                            <pre class="text-red-200 text-sm whitespace-pre-wrap">{{ $this->resultError ?: 'Unknown error' }}</pre>
                        </div>
                    @endif
                </div>
                <div class="p-4 border-t bg-gray-900 flex items-center justify-between">
                    <div class="text-sm text-gray-400">
                        @if ($this->resultCommandId)
                            <span>Command ID: {{ $this->resultCommandId }}</span>
                        @endif
                    </div>
                    <x-filament::button color="gray" wire:click="closeResultModal">Đóng</x-filament::button>
                </div>
            </div>
        </div>
    @endif

    {{-- Mouse Control Modal removed - feature disabled --}}
    @if (false)
        <div class="action-modal-overlay" x-data="{ 
            scale: 1,
            loading: false,
            vncInfo: null,
            vncClient: null,
            useVNC: false,
            rfbModule: null,
            init() {
                // Start polling for VNC info immediately
                this.pollVNCInfo();
                // Wait a bit for VNC to start, then try to connect (but only if VNC info is available)
                setTimeout(() => {
                    if (this.vncInfo) {
                        this.initVNC();
                    } else {
                        console.log('VNC info not ready yet, will retry when available');
                    }
                }, 5000); // Increased to 5 seconds
            },
            async checkVNCInfo() {
                try {
                    const baseUrl = '{{ config('services.python_server.base_url', 'http://127.0.0.1:5000') }}';
                    const apiKey = '{{ config('services.python_server.api_key', '') }}';
                    const response = await fetch(`${baseUrl}/vnc/{{ $this->controlClientId }}`, {
                        headers: { 'X-API-Key': apiKey }
                    });
                    const data = await response.json();
                    if (data.ok && data.vnc) {
                        this.vncInfo = data.vnc;
                        return true;
                    }
                    return false;
                } catch (e) {
                    console.log('VNC info check failed', e);
                    return false;
                }
            },
            pollVNCInfo() {
                // Poll every 2 seconds until VNC info is available
                let pollCount = 0;
                const maxPolls = 30; // 30 * 2s = 60 seconds max
                const pollInterval = setInterval(async () => {
                    pollCount++;
                    const found = await this.checkVNCInfo();
                    if (found && this.vncInfo) {
                        clearInterval(pollInterval);
                        console.log(`VNC info found after ${pollCount * 2} seconds`);
                        // Try to connect VNC if not already connected
                        if (!this.useVNC && !this.loading) {
                            this.initVNC();
                        }
                    } else if (pollCount >= maxPolls) {
                        clearInterval(pollInterval);
                        console.error('VNC info polling timeout after 60 seconds');
                        this.loading = false;
                        alert('VNC server không thể khởi động sau 60 giây. Vui lòng:\n1. Kiểm tra VNC server đã được cài đặt trên client\n2. Kiểm tra client có đang online không\n3. Thử lại sau');
                    }
                }, 2000);
            },
            async initVNC() {
                if (!this.vncInfo) {
                    // Retry getting VNC info
                    await this.checkVNCInfo();
                    if (!this.vncInfo) {
                        console.log('VNC not available, using screenshot fallback');
                        return;
                    }
                }
                
                // Ensure canvas exists
                let canvas = document.getElementById('vnc-canvas');
                if (!canvas) {
                    console.error('VNC canvas not found, creating...');
                    const container = document.getElementById('screen-container');
                    if (container) {
                        const vncDiv = document.createElement('div');
                        vncDiv.setAttribute('x-show', 'useVNC');
                        vncDiv.className = 'border-2 border-gray-600 rounded overflow-hidden bg-black';
                        canvas = document.createElement('canvas');
                        canvas.id = 'vnc-canvas';
                        canvas.className = 'max-w-full h-auto';
                        canvas.style.display = 'block';
                        canvas.style.background = '#000';
                        vncDiv.appendChild(canvas);
                        container.appendChild(vncDiv);
                    } else {
                        console.error('Screen container not found');
                        return;
                    }
                }
                
                try {
                    // Load noVNC as ES module
                    if (!this.rfbModule) {
                        console.log('Loading noVNC as ES module...');
                        this.loading = true;
                        
                        const loadModule = async () => {
                            const moduleSources = [
                                '/js/novnc/rfb.js',
                                'https://cdn.jsdelivr.net/npm/novnc@1.4.0/core/rfb.js',
                                'https://unpkg.com/novnc@1.4.0/core/rfb.js'
                            ];
                            
                            for (const src of moduleSources) {
                                try {
                                    console.log(`Trying to load from: ${src}`);
                                    const module = await import(src);
                                    this.rfbModule = module.default || module.RFB || module;
                                    console.log(`noVNC loaded successfully from: ${src}`);
                                    this.connectVNC();
                                    return;
                                } catch (error) {
                                    console.warn(`Failed to load from ${src}:`, error);
                                }
                            }
                            
                            // All sources failed
                            console.error('Failed to load noVNC from all sources');
                            this.loading = false;
                            alert('Không thể tải noVNC. Vui lòng kiểm tra:\n1. Kết nối internet\n2. Hoặc tải file noVNC về thư mục public/js/novnc/rfb.js');
                        };
                        
                        loadModule();
                    } else {
                        console.log('noVNC module already loaded, connecting...');
                        this.connectVNC();
                    }
                } catch (e) {
                    console.error('Failed to load noVNC:', e);
                    this.loading = false;
                    alert('Lỗi khi tải noVNC: ' + e.message);
                }
            },
            async connectVNC() {
                try {
                    // First check if VNC info is available
                    if (!this.vncInfo) {
                        console.warn('VNC info not available yet, waiting...');
                        // Wait a bit and retry
                        setTimeout(() => {
                            if (this.vncInfo) {
                                this.connectVNC();
                            } else {
                                console.error('VNC info still not available after waiting');
                                this.loading = false;
                                alert('VNC server chưa được khởi động. Vui lòng đợi và thử lại.');
                            }
                        }, 2000);
                        return;
                    }
                    
                    const baseUrl = '{{ config('services.python_server.base_url', 'http://127.0.0.1:5000') }}';
                    const apiKey = '{{ config('services.python_server.api_key', '') }}';
                    const wsUrl = baseUrl.replace('http://', 'ws://').replace('https://', 'wss://') + 
                                  `/vnc/ws/{{ $this->controlClientId }}?api_key=${apiKey}`;
                    
                    console.log('Connecting to VNC WebSocket:', wsUrl);
                    console.log('VNC Info:', this.vncInfo);
                    
                    const canvas = document.getElementById('vnc-canvas');
                    if (!canvas) {
                        console.error('VNC canvas not found');
                        this.loading = false;
                        return;
                    }
                    
                    // Set canvas size
                    canvas.width = 1024;
                    canvas.height = 768;
                    
                    this.loading = true;
                    
                    // Create RFB connection
                    if (!this.rfbModule) {
                        console.error('RFB module not loaded');
                        this.loading = false;
                        return;
                    }
                    
                    const RFBClass = this.rfbModule;
                    this.vncClient = new RFBClass(canvas, wsUrl, {
                        credentials: {
                            password: this.vncInfo?.password || ''
                        },
                        scaleViewport: true,
                        resizeSession: false
                    });
                    
                    // Add connection timeout (give VNC more time to handshake, but don't force close)
                    const connectionTimeout = setTimeout(() => {
                        if (this.loading && !this.useVNC) {
                            console.error('VNC connection timeout (no handshake within 30s)');
                            this.loading = false;
                            alert('Không thể kết nối đến VNC server trong thời gian cho phép.\n'
                                + 'Vui lòng kiểm tra:\n'
                                + '1. Python server có đang chạy không\n'
                                + '2. VNC server trên client đã được start và hoạt động chưa\n'
                                + '3. Firewall có chặn port hoặc IP không');
                            // Không tự disconnect để nếu VNC vẫn đang handshake thì noVNC tự xử lý lỗi
                        }
                    }, 30000); // 30 second timeout
                    
                    this.vncClient.addEventListener('connect', () => {
                        console.log('VNC connected successfully');
                        clearTimeout(connectionTimeout);
                        this.useVNC = true;
                        this.loading = false;
                    });
                    
                    this.vncClient.addEventListener('disconnect', (e) => {
                        console.log('VNC disconnected:', e.detail);
                        clearTimeout(connectionTimeout);
                        this.useVNC = false;
                        this.loading = false;
                        
                        // Show error message if connection failed
                        if (e.detail && e.detail.clean === false) {
                            const reason = e.detail.reason || 'Connection closed unexpectedly';
                            console.error('VNC connection failed:', reason);
                            alert(`Không thể kết nối đến VNC server: ${reason}\n\nVui lòng:\n1. Kiểm tra Python server có đang chạy\n2. Restart VNC server trên client với cấu hình mới\n3. Kiểm tra firewall và network`);
                        }
                    });
                    
                    this.vncClient.addEventListener('credentialsrequired', () => {
                        console.log('VNC requires credentials');
                        // Try to send password if we have it
                        if (this.vncInfo?.password) {
                            this.vncClient.sendCredentials({ password: this.vncInfo.password });
                        }
                    });
                    
                    this.vncClient.addEventListener('securityfailure', (e) => {
                        console.error('VNC security failure:', e.detail);
                        clearTimeout(connectionTimeout);
                        this.loading = false;
                        alert('VNC authentication failed. Vui lòng kiểm tra password.');
                    });
                    
                    this.vncClient.addEventListener('capabilities', (e) => {
                        console.log('VNC capabilities:', e.detail);
                    });
                    
                } catch (e) {
                    console.error('Failed to connect VNC:', e);
                    this.useVNC = false;
                    this.loading = false;
                    alert('Lỗi khi kết nối VNC: ' + e.message);
                }
            },
            disconnectVNC() {
                if (this.vncClient) {
                    this.vncClient.disconnect();
                    this.vncClient = null;
                }
                this.useVNC = false;
            }
        }" x-on:close.window="disconnectVNC()">
            <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" wire:click="closeControl"></div>
            <div class="action-modal-content" style="max-width: 95vw; max-height: 95vh;">
                <div class="relative p-4 border-b flex items-center justify-between bg-gray-900">
                    <div class="flex items-center gap-4">
                        <h3 class="text-xl font-bold text-white">Điều khiển Chuột - {{ $this->controlClientId }}</h3>
                        <x-filament::button size="sm" color="gray" wire:click="fetchScreenshot" 
                            class="!text-white" title="Làm mới màn hình">
                            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15">
                                </path>
                            </svg>
                            Làm mới
                        </x-filament::button>
                    </div>
                    <x-filament::button icon="heroicon-m-x-mark" color="gray" size="sm" wire:click="closeControl"
                        class="!rounded-full !text-white">
                    </x-filament::button>
                </div>
                <div class="p-4 bg-gray-800 overflow-auto" style="max-height: calc(95vh - 80px);">
                    <div class="relative inline-block" id="screen-container">
                        <!-- VNC Canvas (primary) -->
                        <div x-show="useVNC" class="border-2 border-gray-600 rounded overflow-hidden bg-black">
                            <canvas id="vnc-canvas" class="max-w-full h-auto" style="display: block; background: #000;"></canvas>
                            <div x-show="loading" class="absolute inset-0 flex items-center justify-center bg-black/50">
                                <div class="text-center text-white">
                                    <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
                                    <p>Đang kết nối VNC...</p>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Screenshot Fallback -->
                        <div x-show="!useVNC">
                            @if($screenshotBase64)
                                <img id="remote-screen" 
                                    src="data:image/jpeg;base64,{{ $screenshotBase64 }}" 
                                    alt="Remote Screen"
                                    class="max-w-full h-auto border-2 border-gray-600 rounded cursor-crosshair"
                                    style="user-select: none;"
                                    @click="
                                        const img = $el;
                                        const rect = img.getBoundingClientRect();
                                        const scaleX = {{ $screenWidth }} / rect.width;
                                        const scaleY = {{ $screenHeight }} / rect.height;
                                        const x = (event.offsetX) * scaleX;
                                        const y = (event.offsetY) * scaleY;
                                        @this.call('sendMouseClick', x, y, 'left');
                                    "
                                    @contextmenu.prevent="
                                        const img = $el;
                                        const rect = img.getBoundingClientRect();
                                        const scaleX = {{ $screenWidth }} / rect.width;
                                        const scaleY = {{ $screenHeight }} / rect.height;
                                        const x = (event.offsetX) * scaleX;
                                        const y = (event.offsetY) * scaleY;
                                        @this.call('sendMouseClick', x, y, 'right');
                                    "
                                    @dblclick="
                                        const img = $el;
                                        const rect = img.getBoundingClientRect();
                                        const scaleX = {{ $screenWidth }} / rect.width;
                                        const scaleY = {{ $screenHeight }} / rect.height;
                                        const x = (event.offsetX) * scaleX;
                                        const y = (event.offsetY) * scaleY;
                                        @this.call('sendMouseClick', x, y, 'left');
                                        setTimeout(() => @this.call('sendMouseClick', x, y, 'left'), 100);
                                    " />
                            @else
                                <div class="flex items-center justify-center w-full h-96 bg-gray-900 rounded border-2 border-gray-600">
                                    <div class="text-center">
                                        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
                                        <p class="text-white">Đang tải màn hình...</p>
                                        <p class="text-gray-400 text-sm mt-2" x-show="!vncInfo">Đang khởi động VNC server...</p>
                                        <p class="text-gray-400 text-sm mt-2" x-show="vncInfo">VNC đang kết nối...</p>
                                    </div>
                                </div>
                            @endif
                        </div>
                    </div>
                </div>
                <div class="p-4 border-t bg-gray-900 flex items-center justify-between">
                    <div class="flex flex-col gap-2">
                        <div class="text-sm text-gray-400">
                            <span>Click trái: Click chuột trái</span> | 
                            <span>Click phải: Click chuột phải</span> | 
                            <span>Double click: Double click</span>
                        </div>
                        <div x-show="vncInfo" class="text-sm text-green-400">
                            <span x-text="'VNC Server: ' + (vncInfo?.port || 'N/A')"></span>
                            <span x-show="vncInfo?.password_set" class="ml-2">| Password: Set</span>
                            <span class="ml-2">| Connect với VNC client: <span x-text="'{{ $this->controlClientId }}:' + (vncInfo?.port || '5900')"></span></span>
                        </div>
                    </div>
                    <x-filament::button color="gray" wire:click="closeControl">Đóng</x-filament::button>
                </div>
            </div>
        </div>
    @endif

    {{-- Keyboard Control Modal removed - feature disabled --}}
    @if (false)
        <div class="action-modal-overlay" x-data="{ 
            scale: 1,
            loading: false,
            refreshInterval: null,
            init() {
                this.startAutoRefresh();
            },
            startAutoRefresh() {
                this.refreshInterval = setInterval(() => {
                    @this.call('fetchScreenshot');
                }, 500); // Refresh every 0.5 seconds for near real-time
            },
            stopAutoRefresh() {
                if (this.refreshInterval) {
                    clearInterval(this.refreshInterval);
                    this.refreshInterval = null;
                }
            }
        }" x-on:close.window="stopAutoRefresh()">
            <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" wire:click="closeControl"></div>
            <div class="action-modal-content" style="max-width: 95vw; max-height: 95vh;">
                <div class="relative p-4 border-b flex items-center justify-between bg-gray-900">
                    <div class="flex items-center gap-4">
                        <h3 class="text-xl font-bold text-white">Điều khiển Bàn phím - {{ $this->controlClientId }}</h3>
                        <x-filament::button size="sm" color="gray" wire:click="fetchScreenshot" 
                            class="!text-white" title="Làm mới màn hình">
                            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15">
                                </path>
                            </svg>
                            Làm mới
                        </x-filament::button>
                    </div>
                    <x-filament::button icon="heroicon-m-x-mark" color="gray" size="sm" wire:click="closeControl"
                        class="!rounded-full !text-white">
                    </x-filament::button>
                </div>
                <div class="p-4 bg-gray-800 overflow-auto" style="max-height: calc(95vh - 200px);">
                    <div class="relative inline-block" id="screen-container-keyboard">
                        @if($screenshotBase64)
                            <img id="remote-screen-keyboard" 
                                src="data:image/jpeg;base64,{{ $screenshotBase64 }}" 
                                alt="Remote Screen"
                                class="max-w-full h-auto border-2 border-gray-600 rounded"
                                style="user-select: none;" />
                        @else
                            <div class="flex items-center justify-center w-full h-96 bg-gray-900 rounded border-2 border-gray-600">
                                <div class="text-center">
                                    <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
                                    <p class="text-white">Đang tải màn hình...</p>
                                    <p class="text-gray-400 text-sm mt-2">Click vào nút "Làm mới" để lấy màn hình</p>
                                </div>
                            </div>
                        @endif
                    </div>
                </div>
                <div class="p-4 border-t bg-gray-900 space-y-3">
                    <div>
                        <label class="block text-sm font-medium mb-2 text-white">Gõ văn bản (sẽ gửi đến client)</label>
                        <div class="flex gap-2">
                            <input type="text" 
                                wire:model.defer="keyboardText"
                                wire:keydown.enter="sendKeyboardControl"
                                placeholder="Nhập văn bản và nhấn Enter để gửi..."
                                class="flex-1 border border-gray-300 dark:border-gray-700 rounded-lg px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500" />
                            <x-filament::button color="primary" wire:click="sendKeyboardControl">
                                Gửi
                            </x-filament::button>
                        </div>
                    </div>
                    <div class="flex items-center justify-between">
                        <div class="text-sm text-gray-400">
                            <span>Nhập văn bản và nhấn Enter hoặc click "Gửi" để gõ trên client</span>
                        </div>
                        <x-filament::button color="gray" wire:click="closeControl">Đóng</x-filament::button>
                    </div>
                </div>
            </div>
        </div>
    @endif

    {{-- Screenshot Modal --}}
    @if ($this->showScreenshotModal)
        <div class="action-modal-overlay" wire:click="closeScreenshotModal">
            <div class="action-modal-content" style="max-width: 95vw; max-height: 95vh;" wire:click.stop>
                <div class="relative p-4 border-b flex items-center justify-between bg-gray-900">
                    <div class="flex items-center gap-4">
                        <h3 class="text-xl font-bold text-white">Màn hình Client - {{ $this->controlClientId }}</h3>
                        <x-filament::button size="sm" color="gray" wire:click="fetchScreenshot" 
                            class="!text-white" title="Làm mới màn hình">
                            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15">
                                </path>
                            </svg>
                            Làm mới
                        </x-filament::button>
                    </div>
                    <x-filament::button icon="heroicon-m-x-mark" color="gray" size="sm" wire:click="closeScreenshotModal"
                        class="!rounded-full !text-white">
                    </x-filament::button>
                </div>
                <div class="p-4 bg-gray-800 overflow-auto" style="max-height: calc(95vh - 120px);">
                    @if($screenshotBase64)
                        <div class="flex justify-center">
                            <img src="data:image/jpeg;base64,{{ $screenshotBase64 }}" 
                                alt="Client Screenshot"
                                class="max-w-full h-auto border-2 border-gray-600 rounded shadow-lg"
                                style="user-select: none;" />
                        </div>
                        <div class="mt-4 text-center text-sm text-gray-400">
                            <p>Độ phân giải: {{ $screenWidth }}x{{ $screenHeight }}</p>
                        </div>
                    @else
                        <div class="flex items-center justify-center w-full h-96 bg-gray-900 rounded border-2 border-gray-600">
                            <div class="text-center">
                                <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
                                <p class="text-white">Đang chụp màn hình...</p>
                                @if($screenshotCommandId)
                                    <p class="text-gray-400 text-sm mt-2">Command ID: {{ $screenshotCommandId }}</p>
                                @endif
                            </div>
                        </div>
                    @endif
                </div>
                <div class="p-4 border-t bg-gray-900 flex items-center justify-between">
                    <div class="text-sm text-gray-400">
                        <span>Nhấn "Làm mới" để chụp lại màn hình</span>
                    </div>
                    <x-filament::button color="gray" wire:click="closeScreenshotModal">Đóng</x-filament::button>
                </div>
            </div>
        </div>
        
        {{-- Auto-poll for screenshot result --}}
        @if($screenshotCommandId && !$screenshotBase64)
            <div wire:poll.2s="fetchScreenshot"></div>
        @endif
    @endif

    <x-filament::section>
        @if ($this->mode === 'bulk')
            <form wire:submit.prevent="send" class="space-y-6">
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <label class="block">
                        <span class="text-sm font-medium text-gray-700 dark:text-gray-200 mb-1 block">Tìm kiếm</span>
                        <input type="text" wire:model.defer="q" placeholder="client/ip/tag/note"
                            class="w-full border border-gray-300 dark:border-gray-700 rounded-lg px-3 py-2 bg-white dark:bg-gray-900 focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all" />
                    </label>
                    <label class="block">
                        <span class="text-sm font-medium text-gray-700 dark:text-gray-200 mb-1 block">Tag</span>
                        <input type="text" wire:model.defer="tag" placeholder="Nhập tag..."
                            class="w-full border border-gray-300 dark:border-gray-700 rounded-lg px-3 py-2 bg-white dark:bg-gray-900 focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all" />
                    </label>
                    <label class="block">
                        <span class="text-sm font-medium text-gray-700 dark:text-gray-200 mb-1 block">Trạng thái</span>
                        <select wire:model.defer="status"
                            class="w-full border border-gray-300 dark:border-gray-700 rounded-lg px-3 py-2 bg-white dark:bg-gray-900 focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all">
                            <option value="">Tất cả</option>
                            <option value="1">Allow</option>
                            <option value="2">Warning</option>
                            <option value="3">Block</option>
                        </select>
                    </label>
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <label class="block">
                        <span class="text-sm font-medium text-gray-700 dark:text-gray-200 mb-1 block">Hành động</span>
                        <select wire:model.defer="action"
                            class="w-full border border-gray-300 dark:border-gray-700 rounded-lg px-3 py-2 bg-white dark:bg-gray-900 focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all">
                            <option value="">Chọn hành động...</option>
                            <option value="block">Block</option>
                            <option value="unblock">Unblock</option>
                            <option value="notify">Warning</option>
                        </select>
                    </label>
                    <label class="block sm:col-span-2">
                        <span class="text-sm font-medium text-gray-700 dark:text-gray-200 mb-1 block">Message</span>
                        <input type="text" wire:model.defer="message" placeholder="Nhập nội dung tin nhắn..."
                            class="w-full border border-gray-300 dark:border-gray-700 rounded-lg px-3 py-2 bg-white dark:bg-gray-900 focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all" />
                    </label>
                </div>
                <div class="flex items-center gap-3">
                    <x-filament::button type="submit" color="primary" class="px-6">
                        <svg class="w-2.5 h-2.5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
                        </svg>
                        Gửi lệnh
                    </x-filament::button>
                </div>
            </form>
        @else
            <form wire:submit.prevent="send" class="space-y-6">
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <label class="block">
                        <span class="text-sm font-medium text-gray-700 dark:text-gray-200 mb-1 block">Client ID</span>
                        <select wire:model.defer="client_id"
                            class="w-full border border-gray-300 dark:border-gray-700 rounded-lg px-3 py-2 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all">
                            <option value="">Chọn client...</option>
                            @foreach ($this->clientOptions as $opt)
                                <option value="{{ $opt['id'] }}">{{ $opt['label'] }}</option>
                            @endforeach
                        </select>
                    </label>
                    <label class="block">
                        <span class="text-sm font-medium text-gray-700 dark:text-gray-200 mb-1 block">Hành động</span>
                        <select wire:model.defer="action"
                            class="w-full border border-gray-300 dark:border-gray-700 rounded-lg px-3 py-2 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all">
                            <option value="">Chọn hành động...</option>
                            <option value="block">Block</option>
                            <option value="unblock">Unblock</option>
                            <option value="notify">Warning</option>
                        </select>
                    </label>
                    <label class="block">
                        <span class="text-sm font-medium text-gray-700 dark:text-gray-200 mb-1 block">Message</span>
                        <input type="text" wire:model.defer="message" placeholder="Nhập nội dung tin nhắn..."
                            class="w-full border border-gray-300 dark:border-gray-700 rounded-lg px-3 py-2 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all" />
                    </label>
                </div>
                <div class="flex items-center justify-center sm:justify-start">
                    <x-filament::button type="submit" color="primary" class="px-6">
                        <svg class="w-2.5 h-2.5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
                        </svg>
                        Gửi lệnh
                    </x-filament::button>
                </div>
            </form>
        @endif
    </x-filament::section>

    <x-filament::section>
        <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold flex items-center gap-3">
                <svg class="w-1 h-1 text-primary-600 dark:text-primary-400" style="width:16px; height:16px"
                    fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <span>Clients đang online</span>
                <x-filament::badge color="success" size="lg">
                    {{ count($this->onlineClients ?? []) }}
                </x-filament::badge>
            </h3>
            <x-filament::button color="gray" wire:click="loadOnline" class="group">
                <svg class="w-2 h-2 mr-1 group-hover:rotate-180 transition-transform duration-500" fill="none"
                    stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15">
                    </path>
                </svg>
                Làm mới
            </x-filament::button>
        </div>
        <div class="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700"
            wire:poll.10s="loadOnline">
            <table class="min-w-full text-sm border-collapse table-bordered">
                <thead class="bg-gray-50 dark:bg-gray-900/50">
                    <tr>
                        <th
                            class="px-4 py-3 text-left font-semibold text-gray-900 dark:text-gray-100 border-2 border-gray-400 dark:border-gray-600">
                            ClientID
                        </th>
                        <th
                            class="px-4 py-3 text-left font-semibold text-gray-900 dark:text-gray-100 border-2 border-gray-400 dark:border-gray-600">
                            IP
                        </th>
                        <th
                            class="px-4 py-3 text-left font-semibold text-gray-900 dark:text-gray-100 border-2 border-gray-400 dark:border-gray-600">
                            Tags
                        </th>
                        <th
                            class="px-4 py-3 text-left font-semibold text-gray-900 dark:text-gray-100 border-2 border-gray-400 dark:border-gray-600">
                            Actions
                        </th>
                    </tr>
                </thead>
                <tbody class="bg-white dark:bg-gray-800">
                    @forelse(($this->onlineClients ?? []) as $c)
                        <tr class="hover:bg-gray-50 dark:hover:bg-gray-900/30 transition-colors">
                            <td class="px-4 py-3 align-middle border-2 border-gray-400 dark:border-gray-600">
                                <span class="font-medium text-gray-900 dark:text-gray-100">{{ $c['client_id'] }}</span>
                            </td>
                            <td class="px-4 py-3 align-middle border-2 border-gray-400 dark:border-gray-600">
                                <span
                                    class="font-mono text-sm text-gray-700 dark:text-gray-300">{{ $c['ip'] ?? 'N/A' }}</span>
                            </td>
                            <td class="px-4 py-3 align-middle border-2 border-gray-400 dark:border-gray-600">
                                @php
                                    $tags = array_slice((array) ($c['tags'] ?? []), 0, 2);
                                @endphp
                                @if (count($tags) > 0)
                                    @foreach ($tags as $t)
                                        <x-filament::badge color="info"
                                            class="mr-1 mb-1">{{ $t }}</x-filament::badge>
                                    @endforeach
                                @else
                                    <span class="text-gray-400 dark:text-gray-500 text-xs">Không có tag</span>
                                @endif
                            </td>
                            <td class="px-4 py-3 align-middle border-2 border-gray-400 dark:border-gray-600">
                                <x-filament::button size="sm" color="primary"
                                    wire:click="openControl('{{ $c['client_id'] }}')"
                                    class="group hover:scale-105 transition-transform">
                                    <svg class="w-2 h-2 mr-1 inline-block" style="width:16px; height:16px"
                                        fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                            d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4">
                                        </path>
                                    </svg>
                                    Điều khiển
                                </x-filament::button>
                            </td>
                        </tr>
                    @empty
                        <tr>
                            <td class="px-4 py-8 text-center text-gray-500 dark:text-gray-400 border-2 border-gray-400 dark:border-gray-600"
                                colspan="4">
                                <div class="flex flex-col items-center justify-center gap-2">
                                    <svg class="w-8 h-8 text-gray-300 dark:text-gray-600" fill="none"
                                        stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                            d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4">
                                        </path>
                                    </svg>
                                    <span class="text-sm font-medium">Không có client online</span>
                                </div>
                            </td>
                        </tr>
                    @endforelse
                </tbody>
            </table>
        </div>
    </x-filament::section>
</x-filament::page>
