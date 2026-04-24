@extends('layouts.admin')

@section('content')
<h2>Client: {{ $client['client_id'] }}</h2>

<article>
  <p><strong>IP:</strong> {{ $client['ip'] ?? '' }}</p>
  <p><strong>Tags:</strong> {{ implode(',', $client['tags'] ?? []) }}</p>
  <p><strong>Note:</strong> {{ $client['note'] ?? '' }}</p>
  <p><strong>Blocked:</strong> {{ $client['blocked'] ? 'Yes' : 'No' }}</p>
</article>

<div class="grid">
  <article>
    <header>Lịch sử gần đây</header>
    <table>
      <thead>
        <tr>
          <th>ts</th>
          <th>cpu</th>
          <th>network_out</th>
          <th>conn/min</th>
        </tr>
      </thead>
      <tbody>
        @foreach($history as $h)
        <tr>
          <td>{{ $h['ts'] ?? '' }}</td>
          <td>{{ $h['cpu'] ?? '' }}</td>
          <td>{{ $h['network_out'] ?? '' }}</td>
          <td>{{ $h['connections_per_min'] ?? '' }}</td>
        </tr>
        @endforeach
      </tbody>
    </table>
    <form method="post" action="{{ url('/admin/clients/'.$client['client_id'].'/history') }}" onsubmit="return confirm('Xóa lịch sử?')">
      @csrf
      @method('DELETE')
      <button type="submit">Xóa lịch sử</button>
    </form>
  </article>

  <article>
    <header>Hàng đợi lệnh</header>
    <ul>
      @foreach($queue as $q)
        <li>{{ $q['action'] }} - {{ $q['message'] ?? '' }} ({{ $q['source'] }})</li>
      @endforeach
    </ul>
    <form method="post" action="{{ url('/admin/clients/'.$client['client_id'].'/queue') }}" onsubmit="return confirm('Xóa hàng đợi?')">
      @csrf
      @method('DELETE')
      <button type="submit">Xóa hàng đợi</button>
    </form>
  </article>
</div>

@endsection
