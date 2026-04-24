<?php

namespace App\Filament\Widgets;

use App\Models\Client;
use Filament\Widgets\StatsOverviewWidget as BaseWidget;
use Filament\Widgets\StatsOverviewWidget\Stat;

class StatsOverviewWidget extends BaseWidget
{
    protected function getStats(): array
    {
        $totalClients = Client::count();
        $onlineClients = Client::where('online', true)->count();
        $offlineClients = Client::where('online', false)->count();
        $warningClients = Client::where('status', 2)->count();
        $blockedClients = Client::where('status', 3)->count();

        return [
            Stat::make('Tổng số Client', $totalClients)
                ->description('Tổng số máy client trong hệ thống')
                ->descriptionIcon('heroicon-o-computer-desktop')
                ->color('primary')
                ->chart([7, 3, 4, 5, 6, 3, 5]),

            Stat::make('Máy Online', $onlineClients)
                ->description('Số máy đang hoạt động')
                ->descriptionIcon('heroicon-o-signal')
                ->color('success')
                ->chart([2, 3, 4, 3, 4, 5, 4]),

            Stat::make('Máy Offline', $offlineClients)
                ->description('Số máy không hoạt động')
                ->descriptionIcon('heroicon-o-signal-slash')
                ->color('gray')
                ->chart([5, 4, 3, 4, 3, 2, 3]),

            Stat::make('Cảnh báo', $warningClients)
                ->description('Số máy có cảnh báo')
                ->descriptionIcon('heroicon-o-exclamation-triangle')
                ->color('warning')
                ->chart([1, 2, 1, 2, 1, 2, 1]),

            Stat::make('Bị chặn', $blockedClients)
                ->description('Số máy bị chặn')
                ->descriptionIcon('heroicon-o-shield-exclamation')
                ->color('danger')
                ->chart([0, 1, 0, 1, 0, 1, 0]),
        ];
    }
}

