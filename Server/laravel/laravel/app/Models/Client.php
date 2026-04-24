<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class Client extends Model
{
    use HasFactory;

    protected $table = 'clients';

    protected $fillable = [
        'client_id',
        'ip',
        'tags',
        'note',
        'status',
        'online',
        'meta',
        'last_seen_ts',
    ];

    protected $casts = [
        'tags' => 'array',
        'status' => 'integer',
        'online' => 'boolean',
        'meta' => 'array',
        'last_seen_ts' => 'float',
    ];

    public function account()
    {
        return $this->hasOne(ClientAccount::class, 'client_id');
    }
}


