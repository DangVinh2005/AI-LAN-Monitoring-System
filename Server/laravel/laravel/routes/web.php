<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\AdminController;
use App\Http\Controllers\WebhookController;

Route::get('/', fn() => redirect('/admin'));

Route::prefix('admin-api')->group(function () {
    Route::get('/clients', [AdminController::class, 'clients']);
    Route::get('/clients/{id}', [AdminController::class, 'clientShow']);
    Route::patch('/clients/{id}', [AdminController::class, 'clientUpdate']);
    Route::delete('/clients/{id}', [AdminController::class, 'clientDelete']);

    Route::get('/clients/{id}/history', [AdminController::class, 'clientHistory']);
    Route::delete('/clients/{id}/history', [AdminController::class, 'clientHistoryClear']);
    Route::get('/clients/{id}/queue', [AdminController::class, 'clientQueue']);
    Route::delete('/clients/{id}/queue', [AdminController::class, 'clientQueueClear']);

    Route::post('/control', [AdminController::class, 'control']);
    Route::post('/control/bulk', [AdminController::class, 'controlBulk']);
    Route::post('/clients/tags:bulk', [AdminController::class, 'tagsBulk']);

    Route::get('/patterns', [AdminController::class, 'patternsGet']);
    Route::put('/patterns', [AdminController::class, 'patternsPut']);

    Route::get('/logs', [AdminController::class, 'logs']);
    Route::get('/stats', [AdminController::class, 'stats']);

    Route::get('/ai/health', [AdminController::class, 'aiHealth']);
    Route::post('/ai/test', [AdminController::class, 'aiTest']);
});

Route::post('/webhooks/server-events', [WebhookController::class, 'receive']);
