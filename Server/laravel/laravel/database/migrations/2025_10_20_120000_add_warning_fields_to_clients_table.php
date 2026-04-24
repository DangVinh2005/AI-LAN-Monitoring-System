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
        Schema::table('clients', function (Blueprint $table) {
            $table->unsignedInteger('warning_count')->default(0)->after('blocked');
            $table->unsignedInteger('warning_threshold')->nullable()->after('warning_count');
            $table->double('last_warning_ts')->nullable()->after('last_seen_ts');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('clients', function (Blueprint $table) {
            $table->dropColumn(['warning_count', 'warning_threshold', 'last_warning_ts']);
        });
    }
};



