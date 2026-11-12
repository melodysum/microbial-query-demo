import { spawn } from 'node:child_process'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const children = []
function start(command, args) { const child = spawn(command, args, { cwd: root, stdio: 'inherit' }); children.push(child); return child }
function stop() { children.forEach(child => { if (!child.killed) child.kill('SIGTERM') }) }
process.on('SIGINT', () => { stop(); process.exit(1) })
process.on('SIGTERM', () => { stop(); process.exit(1) })
process.env.API_PORT = '8010'
process.env.VERIFY_BASE_URL = 'http://127.0.0.1:17100'
start(path.join(root, '.venv', 'bin', 'python'), ['-m', 'uvicorn', 'backend.main:app', '--host', '127.0.0.1', '--port', '8010'])
start(process.execPath, [path.join(root, 'node_modules', 'vite', 'bin', 'vite.js'), '--host', '127.0.0.1', '--port', '17100'])
await new Promise(resolve => setTimeout(resolve, 3000))
const response = await fetch('http://127.0.0.1:17100/api/library')
console.log('library_api', await response.text())
const verify = start(process.execPath, [path.join(root, 'scripts', 'verify.mjs')])
verify.on('exit', code => { stop(); setTimeout(() => process.exit(code || 0), 300) })
