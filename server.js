import { createServer } from 'http';
import { readFile } from 'fs/promises';
import { join, extname } from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const PORT = 8081;
const FRONTEND_DIR = join(__dirname, 'src', 'frontend');

const mimeTypes = {
    '.html': 'text/html',
    '.js': 'text/javascript',
    '.css': 'text/css',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon'
};

const server = createServer(async (req, res) => {
    console.log(`${req.method} ${req.url}`);
    
    let filePath = join(FRONTEND_DIR, req.url === '/' ? 'index.html' : req.url);
    const ext = String(extname(filePath)).toLowerCase();
    const contentType = mimeTypes[ext] || 'application/octet-stream';
    
    try {
        const content = await readFile(filePath);
        res.writeHead(200, { 
            'Content-Type': contentType,
            'Access-Control-Allow-Origin': '*'
        });
        res.end(content);
    } catch (error) {
        if (error.code === 'ENOENT') {
            res.writeHead(404, { 'Content-Type': 'text/html' });
            res.end('<h1>404 - File Not Found</h1>', 'utf-8');
        } else {
            res.writeHead(500);
            res.end(`Server Error: ${error.code}`, 'utf-8');
        }
    }
});

server.listen(PORT, '0.0.0.0', () => {
    console.log(`\n🚀 SPOTS Server running at:`);
    console.log(`   Local:    http://localhost:${PORT}`);
    console.log(`   Network:  http://0.0.0.0:${PORT}`);
    console.log(`\n📁 Serving files from: ${FRONTEND_DIR}`);
    console.log('\n📄 Available pages:');
    console.log(`   Main:     http://localhost:${PORT}/`);
    console.log(`   Regional: http://localhost:${PORT}/regional-map-optimized.html`);
    console.log('\nPress Ctrl+C to stop the server\n');
});