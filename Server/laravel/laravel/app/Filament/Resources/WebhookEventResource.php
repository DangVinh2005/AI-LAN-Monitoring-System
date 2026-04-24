<?php

namespace App\Filament\Resources;

use App\Filament\Resources\WebhookEventResource\Pages;
use App\Models\WebhookEvent;
use BackedEnum;
use Filament\Resources\Resource;
use Filament\Tables;
use Filament\Tables\Table;

class WebhookEventResource extends Resource
{
    protected static ?string $model = WebhookEvent::class;

    protected static BackedEnum|string|null $navigationIcon = 'heroicon-o-bolt';
    protected static ?string $navigationLabel = 'Webhook Events';

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                Tables\Columns\TextColumn::make('id')->sortable(),
                Tables\Columns\TextColumn::make('type')->searchable()->badge(),
                Tables\Columns\TextColumn::make('received_ts')->sortable(),
            ])
            ->defaultSort('id', 'desc');
    }

    public static function getPages(): array
    {
        return [
            'index' => Pages\ListWebhookEvents::route('/'),
        ];
    }
}


