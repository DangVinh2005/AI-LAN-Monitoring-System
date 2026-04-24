<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration {
    public function up(): void
    {
        Schema::table('clients', function (Blueprint $table) {
            if (!Schema::hasColumn('clients', 'status')) {
                $table->unsignedTinyInteger('status')->default(0)->after('blocked');
            }
        });

        // Backfill: status = 1 if blocked = true; status = 2 if warning_count > 0 and not blocked
        try {
            DB::statement("UPDATE clients SET status = 1 WHERE blocked = 1");
        } catch (\Throwable $e) {
            // ignore
        }
        if (Schema::hasColumn('clients', 'warning_count')) {
            try {
                DB::statement("UPDATE clients SET status = 2 WHERE (blocked = 0 OR blocked IS NULL) AND warning_count > 0");
            } catch (\Throwable $e) {
                // ignore
            }
        }
    }

    public function down(): void
    {
        Schema::table('clients', function (Blueprint $table) {
            if (Schema::hasColumn('clients', 'status')) {
                $table->dropColumn('status');
            }
        });
    }
};


