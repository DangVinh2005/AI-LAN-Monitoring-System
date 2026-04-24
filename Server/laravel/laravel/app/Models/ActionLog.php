<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class ActionLog extends Model
{
    use HasFactory;

    protected $table = 'action_logs';

    protected $fillable = [
        'source',
        'action',
        'client_id',
        'reason',
        'source_user',
        'ts',
        'raw'
    ];

    protected $casts = [
        'ts' => 'float',
        'raw' => 'array',
    ];
}


