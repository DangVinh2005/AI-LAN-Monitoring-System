<?php

namespace App\Http\Controllers;

use App\Models\Client;
use App\Models\ClientAccount;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Str;
use Illuminate\Validation\ValidationException;

class ClientAuthController extends Controller
{
    public function register(Request $request)
    {
        // Entry log to confirm route is hit
        try {
            Log::info('client_register_hit', [
                'path' => $request->path(),
                'ip' => $request->ip(),
            ]);
        } catch (\Throwable $e) {
            // ignore
        }

        try {
            $validated = $request->validate([
                'email' => ['required', 'email', 'max:255', 'unique:client_accounts,email'],
                'password' => ['required', 'string', 'min:6'],
            ]);

            // Create a Client row in the main DB
            $client = Client::create([
                'client_id' => (string) Str::uuid(),
                'ip' => $request->ip(),
            ]);

            $account = ClientAccount::create([
                'client_id' => $client->id,
                'email' => $validated['email'],
                'password' => Hash::make($validated['password']),
            ]);

            // Debug log to verify DB and IDs
            try {
                Log::info('client_register', [
                    'db' => DB::connection()->getDatabaseName(),
                    'client_id' => $client->id,
                    'account_id' => $account->id,
                    'email' => $account->email,
                ]);
            } catch (\Throwable $e) {
                // ignore logging errors
            }

            return response()->json([
                'message' => 'Registered successfully',
                'client' => [
                    'id' => $client->id,
                    'client_id' => $client->client_id,
                ],
                'account' => [
                    'id' => $account->id,
                    'email' => $account->email,
                ],
            ], 201);
        } catch (\Illuminate\Validation\ValidationException $ve) {
            try {
                Log::warning('client_register_validation_failed', [
                    'errors' => $ve->errors(),
                ]);
            } catch (\Throwable $e) {
            }
            return response()->json([
                'message' => 'Validation failed',
                'errors' => $ve->errors(),
            ], 422);
        } catch (\Throwable $e) {
            try {
                Log::error('client_register_error', [
                    'error' => $e->getMessage(),
                ]);
            } catch (\Throwable $e2) {
            }
            return response()->json([
                'message' => 'Registration failed',
            ], 500);
        }
    }

    public function login(Request $request)
    {
        try {
            $validated = $request->validate([
                'email' => ['required', 'email'],
                'password' => ['required', 'string'],
            ]);

            $account = ClientAccount::where('email', $validated['email'])->first();
            if (!$account || !Hash::check($validated['password'], $account->password)) {
                return response()->json([
                    'message' => 'Invalid credentials',
                ], 401);
            }

            // Get or create client record
            $client = Client::find($account->client_id);
            if (!$client) {
                // Client record missing, create one
                $client = Client::create([
                    'client_id' => (string) Str::uuid(),
                    'ip' => $request->ip(),
                ]);
                // Update account to point to new client
                $account->client_id = $client->id;
                $account->save();
            }

            $token = $account->createToken('client-agent')->plainTextToken;

            return response()->json([
                'message' => 'Logged in successfully',
                'token' => $token,
                'client_id' => $client->client_id, // Return client_id (UUID string)
                'account' => [
                    'id' => $account->id,
                    'email' => $account->email,
                ],
            ]);
        } catch (\Illuminate\Validation\ValidationException $ve) {
            try {
                Log::warning('client_login_validation_failed', [
                    'errors' => $ve->errors(),
                ]);
            } catch (\Throwable $e) {
            }
            return response()->json([
                'message' => 'Validation failed',
                'errors' => $ve->errors(),
            ], 422);
        } catch (\Throwable $e) {
            try {
                Log::error('client_login_error', [
                    'error' => $e->getMessage(),
                ]);
            } catch (\Throwable $e2) {
            }
            return response()->json([
                'message' => 'Login failed',
            ], 500);
        }
    }
}


