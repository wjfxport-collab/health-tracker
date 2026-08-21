import fs from 'fs';
import path from 'path';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const certPath = path.resolve(__dirname, '../certs/cert.pem');
const keyPath = path.resolve(__dirname, '../certs/key.pem');
const hasLocalCerts = fs.existsSync(certPath) && fs.existsSync(keyPath);
const isSSL = process.env.ENABLE_SSL === 'true' || process.env.USE_SSL === '1' || process.argv.includes('--ssl');

const backendTarget = process.env.VITE_BACKEND_URL || (isSSL ? 'https://127.0.0.1:5000' : 'http://127.0.0.1:5000');

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    https: (isSSL && hasLocalCerts) ? {
      key: fs.readFileSync(keyPath),
      cert: fs.readFileSync(certPath)
    } : false,
    proxy: {
      '/api': {
        target: backendTarget,
        changeOrigin: true,
        secure: false, // Accepts self-signed certs without throwing validation errors
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, res) => {
            console.error(`[Vite Proxy Error]: Failed to connect to backend at ${backendTarget}:`, err.message);
            if (res.writeHead && !res.headersSent) {
              res.writeHead(502, { 'Content-Type': 'application/json' });
              res.end(JSON.stringify({
                success: false,
                error: `Cannot connect to Python Flask backend at ${backendTarget}.`
              }));
            }
          });
        }
      }
    }
  },
  test: {
    globals: true,
    environment: 'happy-dom',
    setupFiles: './src/setupTests.js',
    css: false
  }
});
