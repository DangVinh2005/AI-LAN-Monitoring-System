<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use App\Http\Controllers\ClientAuthController;
use App\Http\Controllers\ClientApiController;

Route::get('/user', function (Request $request) {
    return $request->user();
})->middleware('auth:sanctum');

Route::post('/client/register', [ClientAuthController::class, 'register']);
Route::post('/client/login', [ClientAuthController::class, 'login']);

Route::middleware('auth:sanctum')->group(function () {
    Route::get('/client/{client_id}/profile', [ClientApiController::class, 'profile']);
    Route::patch('/client/{client_id}/profile', [ClientApiController::class, 'updateProfile']);
    Route::patch('/client/{client_id}/online', [ClientApiController::class, 'updateOnline']);
    Route::patch('/client/{client_id}/client-id', [ClientApiController::class, 'updateClientId']);
});

// Proxy control endpoints to Python server
use App\Http\Controllers\AdminController;
Route::post('/control', [AdminController::class, 'control']);
Route::post('/control/bulk', [AdminController::class, 'controlBulk']);
Route::post('/command/result', function (Request $request) {
    // Forward command result to Python server
    $py = app(\App\Services\PythonServer::class);
    $res = $py->post('/command/result', $request->all());
    return response()->json($res->json());
});
