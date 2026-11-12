import { spawn } from 'node:child_process'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const python = path.join(root, '.venv', 'bin', 'python')
const apiPort = process.env.API_PORT || '8000'
const backend = spawn(python, ['-m', 'uvicorn', 'backend.main:app', '--host', '127.0.0.1', '--port', apiPort], { cwd: root, stdio: 'inherit' })
const args = process.argv.slice(2)
const frontend = spawn(process.execPath, [path.join(root, 'node_modules', 'vite', 'bin', 'vite.js'), ...args], { cwd: root, stdio: 'inherit' })
let stopping = false
function stop(code = 0) {
  if (stopping) return
  stopping = true
  backend.kill('SIGTERM')
  frontend.kill('SIGTERM')
  setTimeout(() => process.exit(code), 250)
}
backend.on('exit', code => { if (!stopping && code) stop(code) })
frontend.on('exit', code => { if (!stopping) stop(code || 0) })
process.on('SIGINT', () => stop(0))
process.on('SIGTERM', () => stop(0))
