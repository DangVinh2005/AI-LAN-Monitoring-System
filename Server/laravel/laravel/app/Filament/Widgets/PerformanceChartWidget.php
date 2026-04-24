<?php

namespace App\Filament\Widgets;

use App\Models\ClientMetric;
use Filament\Widgets\ChartWidget;

class PerformanceChartWidget extends ChartWidget
{
    protected ?string $heading = 'Xu hướng hiệu năng hệ thống';

    protected static ?int $sort = 3;

    protected int | string | array $columnSpan = 'full';

    protected function getData(): array
    {
        // Lấy dữ liệu 7 ngày gần nhất
        $daysAgo = now()->subDays(7)->timestamp;
        
        // Lấy tất cả metrics trong 7 ngày
        $allMetrics = ClientMetric::where('ts', '>=', $daysAgo)
            ->orderBy('ts')
            ->get();

        // Nhóm theo ngày
        $grouped = $allMetrics->groupBy(function ($metric) {
            return date('Y-m-d', (int)$metric->ts);
        });

        $labels = [];
        $cpuData = [];
        $networkData = [];
        $connectionsData = [];

        // Tạo dữ liệu cho 7 ngày gần nhất
        for ($i = 6; $i >= 0; $i--) {
            $date = now()->subDays($i)->format('Y-m-d');
            $dayMetrics = $grouped->get($date, collect());
            
            $labels[] = now()->subDays($i)->format('d/m');
            $cpuData[] = $dayMetrics->isNotEmpty() ? round($dayMetrics->avg('cpu') ?? 0, 2) : 0;
            $networkData[] = $dayMetrics->isNotEmpty() ? round($dayMetrics->avg('network_out') ?? 0, 2) : 0;
            $connectionsData[] = $dayMetrics->isNotEmpty() ? round($dayMetrics->avg('connections_per_min') ?? 0, 2) : 0;
        }

        return [
            'datasets' => [
                [
                    'label' => 'CPU Trung bình (%)',
                    'data' => $cpuData,
                    'backgroundColor' => 'rgba(59, 130, 246, 0.5)',
                    'borderColor' => 'rgb(59, 130, 246)',
                    'fill' => true,
                ],
                [
                    'label' => 'Network Out (MB/s)',
                    'data' => $networkData,
                    'backgroundColor' => 'rgba(16, 185, 129, 0.5)',
                    'borderColor' => 'rgb(16, 185, 129)',
                    'fill' => true,
                ],
                [
                    'label' => 'Connections/phút',
                    'data' => $connectionsData,
                    'backgroundColor' => 'rgba(245, 158, 11, 0.5)',
                    'borderColor' => 'rgb(245, 158, 11)',
                    'fill' => true,
                ],
            ],
            'labels' => $labels,
        ];
    }

    protected function getType(): string
    {
        return 'line';
    }

    protected function getOptions(): array
    {
        return [
            'scales' => [
                'y' => [
                    'beginAtZero' => true,
                ],
            ],
            'plugins' => [
                'legend' => [
                    'display' => true,
                    'position' => 'bottom',
                ],
            ],
        ];
    }
}

