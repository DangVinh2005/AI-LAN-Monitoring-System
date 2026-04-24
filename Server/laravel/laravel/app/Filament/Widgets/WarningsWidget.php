<?php

namespace App\Filament\Widgets;

use App\Models\Client;
use Filament\Tables;
use Filament\Tables\Table;
use Filament\Widgets\TableWidget as BaseWidget;

class WarningsWidget extends BaseWidget
{
    protected int | string | array $columnSpan = 'full';

    protected static ?int $sort = 2;

    public function table(Table $table): Table
    {
        return $table
            ->query(
                Client::query()
                    ->where('status', 2) // Status 2 = warning
                    ->orderBy('last_seen_ts', 'desc')
                    ->limit(10)
            )
            ->columns([
                Tables\Columns\TextColumn::make('client_id')
                    ->label('Client ID')
                    ->searchable()
                    ->sortable(),

                Tables\Columns\TextColumn::make('ip')
                    ->label('IP Address')
                    ->searchable()
                    ->sortable(),

                Tables\Columns\IconColumn::make('online')
                    ->label('Trạng thái')
                    ->boolean()
                    ->trueIcon('heroicon-o-signal')
                    ->falseIcon('heroicon-o-signal-slash')
                    ->trueColor('success')
                    ->falseColor('gray'),

                Tables\Columns\TextColumn::make('last_seen_ts')
                    ->label('Lần cuối hoạt động')
                    ->dateTime('d/m/Y H:i:s')
                    ->sortable(),

                Tables\Columns\TextColumn::make('note')
                    ->label('Ghi chú')
                    ->limit(50)
                    ->tooltip(fn ($record) => $record->note),
            ])
            ->heading('Cảnh báo gần đây')
            ->description('Danh sách các máy client có cảnh báo (tối đa 10 máy)')
            ->emptyStateHeading('Không có cảnh báo')
            ->emptyStateDescription('Hiện tại không có máy client nào có cảnh báo.')
            ->emptyStateIcon('heroicon-o-check-circle');
    }
}

