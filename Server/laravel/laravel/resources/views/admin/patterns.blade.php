@extends('layouts.admin')

@section('content')
<h2>Patterns</h2>
<form method="post" action="{{ url('/admin/patterns') }}">
  @csrf
  @method('PUT')
  <label>
    JSON
    <textarea name="patterns" rows="12">{{ json_encode($patterns ?? [], JSON_PRETTY_PRINT|JSON_UNESCAPED_UNICODE) }}</textarea>
  </label>
  <button type="submit">Lưu</button>
</form>
@endsection
