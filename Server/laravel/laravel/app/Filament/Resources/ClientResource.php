<?php

namespace App\Filament\Resources;

use App\Filament\Resources\ClientResource\Pages;
use App\Models\Client;
use BackedEnum;
use Filament\Resources\Resource;
use Filament\Tables;
use Filament\Tables\Table;
use Illuminate\Support\Facades\Schema;

class ClientResource extends Resource
{
    protected static ?string $model = Client::class;

    protected static BackedEnum|string|null $navigationIcon = 'heroicon-o-users';
    protected static ?string $navigationLabel = 'Clients';

    public static function table(Table $table): Table
    {
        $columns = [
            Tables\Columns\TextColumn::make('client_id')->searchable()->sortable()->label('Client ID'),
            Tables\Columns\TextColumn::make('ip')->searchable()->sortable(),
            Tables\Columns\TagsColumn::make('tags')->label('Tags'),
            Tables\Columns\TextColumn::make('note')->label('Note')->wrap()->toggleable(),
            Tables\Columns\TextColumn::make('meta')
                ->label('Meta')
                ->formatStateUsing(function ($state) {
                    if (is_array($state)) {
                        return $state['os'] ?? json_encode($state, JSON_UNESCAPED_UNICODE);
                    }
                    return (string) $state;
                })
                ->limit(30)
                ->tooltip(fn($state) => is_array($state) ? json_encode($state, JSON_UNESCAPED_UNICODE) : (string) $state)
                ->toggleable(),
            // Multi-state status: 1=allow, 2=warning, 3=block
            Tables\Columns\BadgeColumn::make('status')
                ->label('Trạng thái')
                ->formatStateUsing(function ($state) {
                    $sv = is_numeric($state) ? (int) $state : strtolower((string) $state);
                    if ($sv === 3 || $sv === 'block')
                        return 'block';
                    if ($sv === 2 || $sv === 'warning' || $sv === 'warn')
                        return 'warning';
                    return 'allow';
                })
                ->color(function ($state) {
                    $sv = is_numeric($state) ? (int) $state : strtolower((string) $state);
                    if ($sv === 3 || $sv === 'block')
                        return 'danger';
                    if ($sv === 2 || $sv === 'warning' || $sv === 'warn')
                        return 'warning';
                    return 'success';
                }),
            Tables\Columns\IconColumn::make('online')
                ->boolean()
                ->label('Online'),
        ];

        // Optional legacy columns removed in new schema are no longer shown

        return $table
            ->columns($columns)
            ->filters([
                // Filter by status
                Tables\Filters\SelectFilter::make('status')
                    ->options([
                        1 => 'Allow',
                        2 => 'Warning',
                        3 => 'Block',
                    ]),
            ])
            ->defaultSort('last_seen_ts', 'desc');
    }

    public static function getPages(): array
    {
        return [
            'index' => Pages\ListClients::route('/'),
        ];
    }
}


