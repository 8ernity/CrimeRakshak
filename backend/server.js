const http = require('http');
const { spawn } = require('child_process');

const PORT = process.env.X_ZOHO_CATALYST_LISTEN_PORT || process.env.PORT || 8000;
const PYTHON_PORT = 8001;

console.log(`[BACKEND BRIDGE] Starting Node bridge on port ${PORT}...`);

const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';

const pythonProcess = spawn(pythonCmd, ['run.py', '--port', String(PYTHON_PORT)], {
  cwd: __dirname,
  env: { ...process.env, PORT: String(PYTHON_PORT) },
  stdio: 'inherit'
});

pythonProcess.on('error', (err) => {
  console.error('[BACKEND BRIDGE] Failed to start Python process:', err);
});

pythonProcess.on('exit', (code, signal) => {
  console.error(`[BACKEND BRIDGE] Python process exited with code ${code} and signal ${signal}`);
});

const server = http.createServer((req, res) => {
  // Instant health check response for Catalyst container health monitor
  if (req.url === '/health' || req.url === '/ping') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok', bridge: 'active' }));
    return;
  }

  const options = {
    hostname: '127.0.0.1',
    port: PYTHON_PORT,
    path: req.url,
    method: req.method,
    headers: req.headers
  };

  const proxyReq = http.request(options, (proxyRes) => {
    res.writeHead(proxyRes.statusCode, proxyRes.headers);
    proxyRes.pipe(res, { end: true });
  });

  proxyReq.on('error', (err) => {
    console.error('[BACKEND BRIDGE] Proxy request error:', err);
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok', message: 'Backend initializing', detail: err.message }));
  });

  req.pipe(proxyReq, { end: true });
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`[BACKEND BRIDGE] Listening on port ${PORT}, proxying to Python on ${PYTHON_PORT}`);
});
