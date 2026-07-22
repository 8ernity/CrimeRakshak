const { spawn } = require('child_process');
const http = require('http');
const express = require('express');

const PORT = process.env.X_ZOHO_CATALYST_LISTEN_PORT || process.env.PORT || 8080;
const PYTHON_PORT = 8000;

console.log(`=== Node AppSail Launcher starting on PORT ${PORT} ===`);

let pythonLogs = [];
function logPy(msg) {
  const line = `[${new Date().toISOString()}] ${msg}`;
  console.log(line);
  pythonLogs.push(line);
  if (pythonLogs.length > 100) pythonLogs.shift();
}

// Spawn Python FastAPI server
const pyCmd = process.platform === 'win32' ? 'python' : 'python3';
logPy(`Spawning ${pyCmd} -m uvicorn app.main:app on 127.0.0.1:${PYTHON_PORT}...`);

const py = spawn(pyCmd, ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', String(PYTHON_PORT)], {
  cwd: __dirname,
  env: { ...process.env }
});

py.stdout.on('data', data => logPy(`STDOUT: ${data.toString().trim()}`));
py.stderr.on('data', data => logPy(`STDERR: ${data.toString().trim()}`));
py.on('error', err => logPy(`SPAWN ERROR: ${err.message}`));
py.on('close', code => logPy(`Python process exited with code ${code}`));

const app = express();

// Log inspection endpoint
app.get('/_bridge_logs', (req, res) => {
  res.json({ logs: pythonLogs });
});

// Forward all other requests to Python FastAPI
app.use((req, res) => {
  const proxy = http.request({
    hostname: '127.0.0.1',
    port: PYTHON_PORT,
    path: req.url,
    method: req.method,
    headers: req.headers
  }, (targetRes) => {
    res.writeHead(targetRes.statusCode, targetRes.headers);
    targetRes.pipe(res, { end: true });
  });

  proxy.on('error', (err) => {
    res.status(503).json({
      status: 'starting',
      message: 'FastAPI backend is initializing...',
      error: err.message,
      recent_logs: pythonLogs.slice(-10)
    });
  });

  req.pipe(proxy, { end: true });
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Node AppSail Bridge listening on 0.0.0.0:${PORT} -> 127.0.0.1:${PYTHON_PORT}`);
});
