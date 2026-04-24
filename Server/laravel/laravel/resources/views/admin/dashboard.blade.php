@extends('layouts.admin')

@section('content')
<h2>Dashboard</h2>
<article>
  <ul>
    <li><strong>Clients:</strong> {{ $stats['num_clients'] ?? 0 }}</li>
    <li><strong>Blocked:</strong> {{ $stats['num_blocked'] ?? 0 }}</li>
    <li><strong>Queued Commands:</strong> {{ $stats['num_queued_commands'] ?? 0 }}</li>
    <li><strong>Last Log:</strong> {{ $stats['last_log_ts'] ?? 0 }}</li>
  </ul>
</article>
@endsection
