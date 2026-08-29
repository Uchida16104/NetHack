from __future__ import annotations
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
try:
    from .core import full_report, collect_local
except ImportError:
    from core import full_report, collect_local

HOST, PORT = '127.0.0.1', 8765

class Handler(BaseHTTPRequestHandler):
    server_version = 'NetHackAgent/1.0'
    def _send(self, status: int, body: dict):
        raw = json.dumps(body, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(raw)
    def do_GET(self):
        try:
            q = parse_qs(urlparse(self.path).query)
            if urlparse(self.path).path == '/health':
                return self._send(200, {'ok': True})
            if urlparse(self.path).path == '/collect':
                return self._send(200, collect_local())
            if urlparse(self.path).path == '/report':
                target = q.get('target', [''])[0].strip() or None
                port = int(q['port'][0]) if q.get('port') else None
                return self._send(200, full_report(target, port))
            return self._send(404, {'error': 'not found'})
        except Exception as e:
            return self._send(400, {'error': str(e)})
    def log_message(self, format, *args):
        print(format % args)

if __name__ == '__main__':
    print(f'NetHack local agent listening on http://{HOST}:{PORT}')
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
