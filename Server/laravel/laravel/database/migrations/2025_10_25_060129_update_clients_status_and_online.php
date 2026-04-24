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
            if (!Schema::hasColumn('clients', 'status')) {
                $table->unsignedTinyInteger('status')->default(1)->after('id');
            } else {
                // Ensure default aligns with new semantics: 1 = allow
                try {
                    $table->unsignedTinyInteger('status')->default(1)->change();
                } catch (\Throwable $e) {
                    // Some drivers (e.g. SQLite) may not support change(); ignore
                }
            }

            if (!Schema::hasColumn('clients', 'online')) {
                $table->boolean('online')->default(false)->after('status');
            }
        });

        // Backfill new status semantics and drop legacy columns
        try {
            // Map: blocked -> status = 3 (block); warning_count > 0 -> status = 2; else 1
            if (Schema::hasColumn('clients', 'blocked')) {
                \DB::statement("UPDATE clients SET status = 3 WHERE blocked = 1");
            }
            if (Schema::hasColumn('clients', 'warning_count')) {
                \DB::statement("UPDATE clients SET status = 2 WHERE (status IS NULL OR status = 1) AND warning_count > 0");
            }
            // Default remaining NULL/0 to 1 (allow)
            \DB::statement("UPDATE clients SET status = 1 WHERE status IS NULL OR status = 0");
        } catch (\Throwable $e) {
            // ignore best-effort data backfill
        }

        Schema::table('clients', function (Blueprint $table) {
            foreach (['blocked', 'warning_count', 'warning_threshold', 'last_warning_ts'] as $col) {
                if (Schema::hasColumn('clients', $col)) {
                    $table->dropColumn($col);
                }
            }
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('clients', function (Blueprint $table) {
            if (!Schema::hasColumn('clients', 'blocked')) {
                $table->boolean('blocked')->default(false)->after('note');
            }
            if (!Schema::hasColumn('clients', 'warning_count')) {
                $table->unsignedInteger('warning_count')->default(0)->after('blocked');
            }
            if (!Schema::hasColumn('clients', 'warning_threshold')) {
                $table->unsignedInteger('warning_threshold')->nullable()->after('warning_count');
            }
            if (!Schema::hasColumn('clients', 'last_warning_ts')) {
                $table->double('last_warning_ts')->nullable()->after('last_seen_ts');
            }
        });

        // Reverse-map status back into legacy fields
        try {
            \DB::statement("UPDATE clients SET blocked = 1 WHERE status = 3");
            \DB::statement("UPDATE clients SET warning_count = 1 WHERE status = 2");
        } catch (\Throwable $e) {
            // ignore
        }

        Schema::table('clients', function (Blueprint $table) {
            if (Schema::hasColumn('clients', 'online')) {
                $table->dropColumn('online');
            }
            // Restore prior default if needed
            try {
                $table->unsignedTinyInteger('status')->default(0)->change();
            } catch (\Throwable $e) {
                // ignore if not supported
            }
        });
    }
};
