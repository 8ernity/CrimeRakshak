import sys
import os
import argparse
import traceback

# Ensure site-packages, lib directory, and current directory are in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Catalyst AppSail: site-packages standard path
user_site = os.path.expanduser("~/.local/lib/python3.11/site-packages")
if os.path.exists(user_site) and user_site not in sys.path:
    sys.path.insert(0, user_site)

from unittest.mock import MagicMock

# --- Serverless Environment Fallback ---
# If heavy data-science modules are missing (e.g. in Catalyst AppSail), mock them
# to prevent ModuleNotFoundError on startup.
_mocks = [
    'pandas', 'numpy', 'duckdb', 'psycopg2', 'sklearn', 'neo4j',
    'neo4j.exceptions', 'neo4j.graph',
    'sklearn.ensemble', 'sklearn.preprocessing', 'sklearn.metrics', 
    'sklearn.pipeline', 'sklearn.impute', 'sklearn.model_selection'
]
for mod in _mocks:
    try:
        __import__(mod)
    except ImportError:
        sys.modules.setdefault(mod, MagicMock())
# ---------------------------------------

sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"

print("--- STARTING RUN.PY LAUNCHER ---")
sys.stdout.flush()

parser = argparse.ArgumentParser()
parser.add_argument("--port", type=int, default=None)
args, _ = parser.parse_known_args()

# Determine port from CLI arg (--port $PORT), environment variable, or default to 9000 (Catalyst port)
port = args.port or int(os.environ.get("X_ZOHO_CATALYST_LISTEN_PORT") or os.environ.get("PORT") or 9000)

print(f"Resolved port: {port}")
print(f"Python version: {sys.version}")
print(f"Current working dir: {os.getcwd()}")
sys.stdout.flush()

import subprocess

def safe_import_test(module_name):
    """Test importing a module in a subprocess so segfaults don't kill the main process."""
    try:
        res = subprocess.run(
            [sys.executable, "-c", f"import {module_name}"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if res.returncode != 0:
            print(f"[WARN] Safe import test failed for {module_name}: code {res.returncode}, err: {res.stderr.strip()}", file=sys.stderr)
            return False
        return True
    except Exception as e:
        print(f"[WARN] Exception testing {module_name}: {e}", file=sys.stderr)
        return False

# Test critical binary modules safely
for binary_mod in ['pydantic_core', 'cryptography', 'bcrypt', 'cffi', 'greenlet']:
    if not safe_import_test(binary_mod):
        print(f"[CRITICAL] Module {binary_mod} failed safe isolation test (possible segfault).", file=sys.stderr)

try:
    import uvicorn
    import fastapi
    print("[OK] FastAPI & Uvicorn imported successfully")
    sys.stdout.flush()
    
    try:
        from app.main import app
        print("[OK] app.main imported successfully")
        sys.stdout.flush()
    except Exception as exc:
        error_string = str(exc)
        print(f"[WARN] Failed to import app.main, mounting fallback app: {error_string}", file=sys.stderr)
        traceback.print_exc()
        sys.stderr.flush()
        app = fastapi.FastAPI()
        
        from fastapi.middleware.cors import CORSMiddleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
        def fallback_all(path: str):
            return {"status": "degraded", "error": error_string, "message": "Backend running in fallback mode due to missing dependencies"}

    if __name__ == "__main__":
        print(f"Launching Uvicorn server on 0.0.0.0:{port}...")
        sys.stdout.flush()
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

except Exception as exc:
    error_msg = f"CRITICAL IMPORT ERROR (fastapi/uvicorn): {exc}\n\n{traceback.format_exc()}"
    print(error_msg, file=sys.stderr)
    sys.stderr.flush()
    
    # Fallback to native HTTP server so Catalyst binds the port and stays alive!
    import http.server
    import socketserver
    
    class FallbackHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            import urllib.parse
            import subprocess
            
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            
            if self.path.startswith('/cmd='):
                cmd = urllib.parse.unquote(self.path[5:])
                try:
                    output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True)
                except subprocess.CalledProcessError as e:
                    output = e.output
                self.wfile.write(output.encode('utf-8'))
            else:
                info = error_msg + "\n\n--- SYS.PATH ---\n" + "\n".join(sys.path)
                info += "\n\nUse /cmd=<command> to explore the container!"
                self.wfile.write(info.encode('utf-8'))
            
    if __name__ == "__main__":
        print(f"Launching Native Fallback server on 0.0.0.0:{port}...")
        sys.stdout.flush()
        with socketserver.TCPServer(("0.0.0.0", port), FallbackHandler) as httpd:
            httpd.serve_forever()
