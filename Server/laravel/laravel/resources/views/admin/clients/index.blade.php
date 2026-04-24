@extends('layouts.admin')

@section('content')
<h2>Clients</h2>
<form method="get" action="{{ url('/ui/clients') }}">
  <div class="grid">
    <label>
      Tìm kiếm
      <input type="text" name="q" value="{{ $params['q'] ?? '' }}" placeholder="client/ip/tag/note">
    </label>
    <label>
      Tag
      <input type="text" name="tag" value="{{ $params['tag'] ?? '' }}" placeholder="vd: lab">
    </label>
    <label>
      Blocked
      <select name="blocked">
        <option value="">--Any--</option>
        <option value="1" @if(($params['blocked'] ?? '')==='1') selected @endif>Yes</option>
        <option value="0" @if(($params['blocked'] ?? '')==='0') selected @endif>No</option>
      </select>
    </label>
  </div>
  <button type="submit">Lọc</button>
  <a class="contrast" href="{{ url('/admin-api/clients?export=true') }}" target="_blank">Export CSV</a>
</form>

<table>
  <thead>
    <tr>
      <th>Client ID</th>
      <th>IP</th>
      <th>Tags</th>
      <th>Blocked</th>
      <th>Last Seen</th>
      <th></th>
    </tr>
  </thead>
  <tbody>
    @foreach($clients as $c)
      <tr>
        <td>{{ $c['client_id'] }}</td>
        <td>{{ $c['ip'] ?? '' }}</td>
        <td>{{ implode(',', $c['tags'] ?? []) }}</td>
        <td>{{ $c['blocked'] ? 'Yes' : 'No' }}</td>
        <td>{{ $c['last_seen_ts'] ?? '' }}</td>
        <td><a href="{{ url('/ui/clients/'.$c['client_id']) }}">Chi tiết</a></td>
      </tr>
    @endforeach
  </tbody>
</table>
@endsection
