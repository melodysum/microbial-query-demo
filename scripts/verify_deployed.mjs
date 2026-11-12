import { spawn } from 'node:child_process'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const tunnel = spawn('ssh', ['-N', '-T', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', '-L', '7100:127.0.0.1:7100', 'iyun188-512G'], { stdio: 'inherit' })
let finished = false
function stop(code) { if (finished) return; finished = true; tunnel.kill('SIGTERM'); setTimeout(() => process.exit(code), 250) }
tunnel.on('exit', code => { if (!finished) stop(code || 1) })
process.on('SIGINT', () => stop(1))
process.on('SIGTERM', () => stop(1))
await new Promise(resolve => setTimeout(resolve, 2500))
const response = await fetch('http://127.0.0.1:7100/api/health')
if (!response.ok) throw new Error(`HTTP ${response.status}`)
console.log('deployed_health', await response.text())
const verify = spawn(process.execPath, [path.join(root, 'scripts', 'verify.mjs')], { cwd: root, stdio: 'inherit' })
verify.on('exit', code => stop(code || 0))
