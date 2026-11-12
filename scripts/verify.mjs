import { chromium } from 'playwright'
import fs from 'node:fs'
import path from 'node:path'

const root = path.resolve(new URL('..', import.meta.url).pathname)
const qa = path.join(root, 'qa')
fs.mkdirSync(qa, { recursive: true })
const browser = await chromium.launch({ headless: true, executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', args: ['--no-proxy-server'] })
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1 })
const errors = []
const missing = []
page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()) })
page.on('response', response => { if (response.status() === 404) missing.push(response.url()) })
const report = {}
try {
  await page.goto('http://127.0.0.1:7100', { waitUntil: 'networkidle' })
  await page.screenshot({ path: path.join(qa, 'desktop.png'), fullPage: true })
  report.title = await page.locator('h1').first().textContent()
  report.initialRows = await page.locator('.result-table tbody tr').count()

  await page.getByRole('button', { name: '自然语言', exact: true }).click()
  await page.getByRole('button', { name: '解析查询', exact: true }).click()
  await page.locator('.parse-result').waitFor()
  const searchResponse = page.waitForResponse(r => r.url().includes('/api/search') && r.request().method() === 'POST')
  await page.getByRole('button', { name: '按明确条件查询', exact: true }).click()
  await searchResponse
  await page.waitForTimeout(400)
  report.naturalRows = await page.locator('.result-table tbody tr').count()

  await page.getByRole('button', { name: '证据文献库', exact: true }).click()
  await page.waitForTimeout(400)
  report.coreLiterature = await page.locator('.literature-item').count()
  const shareResponse = page.waitForResponse(r => r.url().includes('/api/literature') && r.url().includes('share_lead'))
  await page.getByRole('button', { name: '分享线索', exact: true }).click()
  await shareResponse
  await page.waitForTimeout(300)
  report.shareLeads = await page.locator('.literature-item').count()
  await page.screenshot({ path: path.join(qa, 'literature.png'), fullPage: true })

  await page.getByRole('button', { name: '查询工作台', exact: true }).click()
  await page.getByRole('button', { name: '序列近邻', exact: true }).click()
  await page.locator('input[type=file]').setInputFiles(path.join(root, 'data/genomes/GCA_000158015.1_ASM15801v1_genomic.fna.gz'))
  const sequenceResponse = page.waitForResponse(r => r.url().includes('/api/sequence/search'), { timeout: 120000 })
  await page.getByRole('button', { name: '开始近邻检索', exact: true }).click()
  await sequenceResponse
  await page.locator('.sequence-result').waitFor({ timeout: 120000 })
  report.sequenceMethod = await page.locator('.sequence-result .text-sm').textContent()
  report.sequenceTop = await page.locator('.match-row').first().textContent()
  await page.screenshot({ path: path.join(qa, 'sequence.png'), fullPage: true })

  await page.setViewportSize({ width: 375, height: 812 })
  await page.goto('http://127.0.0.1:7100', { waitUntil: 'networkidle' })
  report.mobileOverflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)
  await page.screenshot({ path: path.join(qa, 'mobile.png'), fullPage: true })
  report.consoleErrors = errors
  report.http404 = missing
} catch (error) {
  report.fatal = String(error)
  await page.screenshot({ path: path.join(qa, 'failure.png'), fullPage: true }).catch(() => {})
} finally {
  await browser.close()
}
fs.writeFileSync(path.join(qa, 'report.json'), JSON.stringify(report, null, 2))
console.log(JSON.stringify(report, null, 2))
