import http.server
import threading

import pytest


@pytest.fixture
def http_server():
    """A local server that records every request, to prove alihrupa never downloads anything (G-001)."""
    requests = []

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append(self.path)
            self.send_error(404)

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}", requests
    server.shutdown()
