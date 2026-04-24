@extends('layouts.admin')

@section('content')
<h2>Logs</h2>
<table>
  <thead>
    <tr>
      <th>ts</th>
      <th>source</th>
      <th>action</th>
      <th>client_id</th>
      <th>reason</th>
    </tr>
  </thead>
  <tbody>
    @foreach($items as $it)
    <tr>
      <td>{{ $it['ts'] ?? '' }}</td>
      <td>{{ $it['source'] ?? '' }}</td>
      <td>{{ $it['action'] ?? '' }}</td>
      <td>{{ $it['client_id'] ?? '' }}</td>
      <td>{{ $it['reason'] ?? '' }}</td>
    </tr>
    @endforeach
  </tbody>
</table>
@endsection
