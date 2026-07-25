const path = require('path');
const PORT = process.env.X_ZOHO_CATALYST_LISTEN_PORT || process.env.PORT || 9000;
process.env.PORT = PORT;
process.env.HOSTNAME = '0.0.0.0';

const standalonePath = path.join(__dirname, '.next', 'standalone');
console.log(`Setting working directory to ${standalonePath}...`);
process.chdir(standalonePath);

console.log(`Starting Next.js Server on PORT ${PORT}...`);
require(path.join(standalonePath, 'server.js'));
