<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration {
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::create('client_metrics', function (Blueprint $table) {
            $table->id();
            $table->string('client_id')->index();
            $table->float('cpu');
            $table->float('network_out');
            $table->integer('connections_per_min');
            $table->integer('uptime_sec')->nullable();
            $table->double('ts')->index();
            $table->json('meta')->nullable();
            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('client_metrics');
    }
};


