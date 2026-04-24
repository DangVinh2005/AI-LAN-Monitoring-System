<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;

class PythonServer
{
    protected string $baseUrl;
    protected ?string $apiKey;
    protected ?\Illuminate\Http\Client\PendingRequest $client = null;

    public function __construct()
    {
        $this->baseUrl = rtrim(config('services.python_server.base_url', env('PY_SERVER_URL', 'http://localhost:5000')), '/');
        $this->apiKey = config('services.python_server.api_key', env('ADMIN_API_KEY'));
    }

    /**
     * Get or create a reusable HTTP client with connection pooling
     * This improves performance by reusing connections
     */
    protected function client(): \Illuminate\Http\Client\PendingRequest
    {
        if ($this->client === null) {
            $this->client = Http::withHeaders($this->withAuth())
                ->timeout(5) // Reduced timeout for faster failures
                ->connectTimeout(2); // Fast connection timeout
        }
        return $this->client;
    }

    protected function withAuth(array $headers = []): array
    {
        if ($this->apiKey) {
            $headers['X-API-Key'] = $this->apiKey;
        }
        return $headers;
    }

    public function get(string $path, array $query = [])
    {
        return $this->client()
            ->get($this->baseUrl . $path, $query)
            ->throw();
    }

    public function post(string $path, array $data = [])
    {
        return $this->client()
            ->post($this->baseUrl . $path, $data)
            ->throw();
    }

    public function patch(string $path, array $data = [])
    {
        return $this->client()
            ->patch($this->baseUrl . $path, $data)
            ->throw();
    }

    public function put(string $path, array $data = [])
    {
        return $this->client()
            ->put($this->baseUrl . $path, $data)
            ->throw();
    }

    public function delete(string $path, array $query = [])
    {
        return $this->client()
            ->delete($this->baseUrl . $path, $query)
            ->throw();
    }
}
