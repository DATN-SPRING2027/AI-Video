import { createServer } from 'node:http'
import { readFile } from 'node:fs/promises'
import { dirname, extname, join, normalize } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = dirname(fileURLToPath(import.meta.url))
const PORT = Number(process.env.PORT || 8793)
const TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
}

createServer(async (req, res) => {
  const clean = normalize(decodeURIComponent(new URL(req.url || '/', 'http://localhost').pathname)).replace(/^(\.\.[/\\])+/, '')
  const target = join(root, clean === '/' || clean === '\\' ? 'index.html' : clean)
  try {
    const body = await readFile(target)
    res.writeHead(200, { 'content-type': TYPES[extname(target)] || 'application/octet-stream', 'cache-control': 'no-store' })
    res.end(body)
  } catch {
    res.writeHead(404)
    res.end('Not found')
  }
}).listen(PORT, '127.0.0.1', () => {
  console.log(`CreateVideo 2D/3D Knowledge Graph running at http://127.0.0.1:${PORT}`)
})

