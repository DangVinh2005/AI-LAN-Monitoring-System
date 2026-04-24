<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Admin</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css">
  </head>
  <body>
    <nav class="container">
      <ul>
        <li><strong>Server–Client Manager</strong></li>
      </ul>
      <ul>
        <li><a href="{{ url('/ui') }}">Dashboard</a></li>
        <li><a href="{{ url('/ui/clients') }}">Clients</a></li>
        <li><a href="{{ url('/ui/logs') }}">Logs</a></li>
        <li><a href="{{ url('/ui/patterns') }}">Patterns</a></li>
        <li><a href="{{ url('/ui/ai') }}">AI</a></li>
      </ul>
    </nav>
    <main class="container">
      @yield('content')
    </main>
  </body>
</html>
