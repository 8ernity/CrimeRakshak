const PORT = process.env.X_ZOHO_CATALYST_LISTEN_PORT || process.env.PORT || 3000;
process.env.PORT = PORT;
process.env.HOSTNAME = '0.0.0.0';

console.log(`Starting Next.js Server on PORT ${PORT}...`);
require('./.next/standalone/server.js');
