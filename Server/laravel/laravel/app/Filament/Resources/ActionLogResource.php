<?php

namespace App\Filament\Resources;

use App\Filament\Resources\ActionLogResource\Pages;
use App\Models\ActionLog;
use BackedEnum;
use Filament\Resources\Resource;
use Filament\Tables;
use Filament\Tables\Table;

class ActionLogResource extends Resource
{
    protected static ?string $model = ActionLog::class;

    protected static BackedEnum|string|null $navigationIcon = 'heroicon-o-queue-list';
    protected static ?string $navigationLabel = 'Action Logs';

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                Tables\Columns\TextColumn::make('ts')->sortable(),
                Tables\Columns\TextColumn::make('source')->badge(),
                Tables\Columns\TextColumn::make('action')->searchable(),
                Tables\Columns\TextColumn::make('client_id')->searchable(),
                Tables\Columns\TextColumn::make('reason')->limit(60),
            ])
            ->defaultSort('ts', 'desc');
    }

    public static function getPages(): array
    {
        return [
            'index' => Pages\ListActionLogs::route('/'),
        ];
    }
}


