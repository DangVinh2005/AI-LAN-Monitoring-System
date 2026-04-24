<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class WebhookEvent extends Model
{
    use HasFactory;

    protected $table = 'webhook_events';

    protected $fillable = [
        'type',
        'data',
        'received_ts'
    ];

    protected $casts = [
        'data' => 'array',
        'received_ts' => 'float',
    ];
}


