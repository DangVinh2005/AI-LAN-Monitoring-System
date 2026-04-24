<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class ClientMetric extends Model
{
    use HasFactory;

    protected $table = 'client_metrics';

    protected $fillable = [
        'client_id',
        'cpu',
        'network_out',
        'connections_per_min',
        'uptime_sec',
        'ts',
        'meta'
    ];

    protected $casts = [
        'cpu' => 'float',
        'network_out' => 'float',
        'connections_per_min' => 'integer',
        'uptime_sec' => 'integer',
        'ts' => 'float',
        'meta' => 'array',
    ];
}


