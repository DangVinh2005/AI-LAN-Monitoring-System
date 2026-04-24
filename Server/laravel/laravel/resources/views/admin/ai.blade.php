@extends('layouts.admin')

@section('content')
<h2>AI</h2>

<article>
  <p><strong>AI Health:</strong> {{ ($health['ok'] ?? false) ? 'OK' : 'DOWN' }}</p>
</article>

<article>
  <header>Test AI Analyze</header>
  <form method="post" action="{{ url('/ui/ai/test') }}">
    @csrf
    <div class="grid">
      <label>
        client_id
        <input name="client_id" value="{{ $input['client_id'] ?? '' }}" required>
      </label>
      <label>
        cpu
        <input type="number" step="0.01" name="cpu" value="{{ $input['cpu'] ?? 10 }}">
      </label>
      <label>
        network_out
        <input type="number" step="0.01" name="network_out" value="{{ $input['network_out'] ?? 50 }}">
      </label>
      <label>
        connections_per_min
        <input type="number" name="connections_per_min" value="{{ $input['connections_per_min'] ?? 5 }}">
      </label>
    </div>
    <button type="submit">Gửi</button>
  </form>
  @if(isset($result))
  <pre>{{ json_encode($result, JSON_PRETTY_PRINT|JSON_UNESCAPED_UNICODE) }}</pre>
  @endif
</article>
@endsection


