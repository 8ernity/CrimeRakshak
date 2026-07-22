import http.server
import socketserver
import os
import sys

port = int(os.environ.get("X_ZOHO_CATALYST_LISTEN_PORT") or os.environ.get("PORT") or 8080)
print(f"=== TEST SERVER STARTING ON PORT {port} ===", flush=True)

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        msg = f'{{"status":"ok","service":"test_server","port":{port}}}'
        self.wfile.write(msg.encode("utf-8"))

with socketserver.TCPServer(("0.0.0.0", port), Handler) as httpd:
    httpd.serve_forever()
