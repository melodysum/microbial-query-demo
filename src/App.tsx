import { useEffect, useMemo, useState } from 'react'
import {
  AlertTriangle, BookOpen, CheckCircle2, ChevronDown, ChevronRight, Database,
  Dna, Download, FileText, FlaskConical, Info, Loader2, Menu, Microscope,
  Plus, Search, Upload, X, Languages,
} from 'lucide-react'
import { api } from './api'
import { english } from './i18n'
import type { Feature, Filter, Health, Literature, Observation, SearchResponse, SequenceMatch, Strain, Taxon } from './types'
import './App.css'
import './academic.css'

const featureLabels: Record<string, string> = {
  species: '物种', name: '名称', gram_stain: '革兰氏染色', oxygen_requirement: '需氧性',
  nacl_growth_max: '最高耐盐浓度', isolation_habitat: '分离环境', salt_tolerance_description: '耐盐描述',
}
const valueLabels: Record<string, string> = {
  positive: '阳性', negative: '阴性', anaerobe: '厌氧', aerobe: '好氧', facultative_anaerobe: '兼性厌氧',
  true: '是', false: '否', rod: '杆状', coccus: '球状', human_gut: '人肠道', marine_sediment: '海洋沉积物', soil: '土壤', fermented_food: '发酵食品',
}
const label = (key: string) => featureLabels[key] || key
const displayValue = (value: unknown) => valueLabels[String(value)] || String(value)

function TaxonNode({ node, depth, selected, onSelect, t }: { node: Taxon; depth: number; selected: string; onSelect: (species: string) => void; t: (text: string) => string }) {
  const [open, setOpen] = useState(depth < 3)
  const isSpecies = node.children.length === 0
  return (
    <div>
      <div className="flex items-center gap-1" style={{ paddingLeft: `${depth * 10}px` }}>
        {!isSpecies ? (
          <button className="tree-toggle" onClick={() => setOpen(!open)} aria-label={t(open ? '收起' : '展开')}>
            {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          </button>
        ) : <span className="w-5" />}
        <button
          className={`tree-item ${selected === node.name ? 'active' : ''}`}
          onClick={() => isSpecies ? onSelect(node.name) : setOpen(!open)}
        >
          <span className="truncate">{node.name}</span><span className="tree-count">{node.count}</span>
        </button>
      </div>
      {open && node.children.map(child => <TaxonNode key={child.name} node={child} depth={depth + 1} selected={selected} onSelect={onSelect} t={t} />)}
    </div>
  )
}

function ResultTable({ items, onSelect, t }: { items: Strain[]; onSelect: (id: string) => void; t: (text: string) => string }) {
  return (
    <div className="overflow-x-auto">
      <table className="result-table">
        <thead><tr><th>{t('菌株')}</th><th>{t('物种')}</th><th>Accession</th><th>{t('匹配情况')}</th><th /></tr></thead>
        <tbody>{items.map(strain => (
          <tr key={strain.id} onClick={() => onSelect(strain.id)} className="cursor-pointer">
            <td className="font-medium text-slate-900">{strain.strain_name}</td>
            <td className="italic">{strain.species}</td>
            <td className="font-mono text-xs">{strain.accession}</td>
            <td><div className="flex flex-wrap gap-1">{strain.match_reasons?.slice(0, 3).map((r, i) => (
              <span key={i} className={`reason-chip ${r.status}`}>{t(r.label)}: {r.observed == null ? t('未知') : t(displayValue(r.observed))}</span>
            ))}</div></td>
            <td><ChevronRight size={16} className="text-slate-400" /></td>
          </tr>
        ))}</tbody>
      </table>
    </div>
  )
}

export default function App() {
  const [health, setHealth] = useState<Health | null>(null)
  const [features, setFeatures] = useState<Feature[]>([])
  const [tree, setTree] = useState<Taxon | null>(null)
  const [view, setView] = useState<'search' | 'literature'>('search')
  const [tab, setTab] = useState<'filters' | 'natural' | 'sequence'>('filters')
  const [filters, setFilters] = useState<Filter[]>([])
  const [results, setResults] = useState<SearchResponse>({ confirmed: [], possible: [], counts: { confirmed: 0, possible: 0 } })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [newFeature, setNewFeature] = useState('gram_stain')
  const [newOperator, setNewOperator] = useState('eq')
  const [newValue, setNewValue] = useState('negative')
  const [naturalText, setNaturalText] = useState('Find Gram-negative, facultatively anaerobic E. coli with NaCl tolerance ≥3%')
  const [parsed, setParsed] = useState<any>(null)
  const [selectedStrain, setSelectedStrain] = useState<string | null>(null)
  const [observations, setObservations] = useState<Observation[]>([])
  const [sequenceFile, setSequenceFile] = useState<File | null>(null)
  const [sequenceResult, setSequenceResult] = useState<any>(null)
  const [selectedLibrary, setSelectedLibrary] = useState('demo')
  const [libraryStatus, setLibraryStatus] = useState<any>(null)
  const [literature, setLiterature] = useState<Literature[]>([])
  const [literatureType, setLiteratureType] = useState('core')
  const [literatureQuery, setLiteratureQuery] = useState('')
  const [mobileTree, setMobileTree] = useState(false)
  const [catalog, setCatalog] = useState<Strain[]>([])
  const [lang, setLang] = useState<'en' | 'zh'>(() => (localStorage.getItem('microbial-language') as 'en' | 'zh') || 'en')
  const T = (text: string) => lang === 'en' ? (english[text] || text) : text
  const toggleLang = () => {
    const next = lang === 'en' ? 'zh' : 'en'
    setLang(next)
    localStorage.setItem('microbial-language', next)
  }

  const currentFeature = features.find(f => f.key === newFeature)
  const selectedStrainData = useMemo(() => catalog.find(s => s.id === selectedStrain), [catalog, selectedStrain])

  async function runSearch(next = filters) {
    setLoading(true); setError('')
    try {
      const data = await api<SearchResponse>('/search', { method: 'POST', body: JSON.stringify({ filters: next }) })
      setResults(data)
    } catch (e) { setError(T((e as Error).message)) } finally { setLoading(false) }
  }

  async function loadLiterature(type = literatureType, q = literatureQuery) {
    const data = await api<{ records: Literature[] }>(`/literature?record_type=${type}&q=${encodeURIComponent(q)}`)
    setLiterature(data.records)
  }

  useEffect(() => {
    Promise.all([
      api<Health>('/health'), api<{ features: Feature[] }>('/features'), api<{ tree: Taxon }>('/taxonomy/tree'), api<{ strains: Strain[] }>('/strains'), api('/library'),
    ]).then(([h, f, t, s, l]) => { setHealth(h); setFeatures(f.features); setTree(t.tree); setCatalog(s.strains); setLibraryStatus(l) }).catch(e => setError(T(e.message)))
    runSearch([])
  }, [])
  useEffect(() => { document.documentElement.lang = lang === 'en' ? 'en' : 'zh-CN' }, [lang])
  useEffect(() => { loadLiterature() }, [literatureType])
  useEffect(() => {
    if (!selectedStrain) return
    api<{ observations: Observation[] }>(`/strains/${selectedStrain}`).then(d => setObservations(d.observations)).catch(e => setError(T(e.message)))
  }, [selectedStrain])
  useEffect(() => {
    const close = (e: KeyboardEvent) => { if (e.key === 'Escape') { setSelectedStrain(null); setMobileTree(false) } }
    window.addEventListener('keydown', close)
    return () => window.removeEventListener('keydown', close)
  }, [])

  function addFilter() {
    if (newValue === '') return
    const next = [...filters, { feature: newFeature, operator: newOperator, value: newValue, unit: currentFeature?.unit || '' }]
    setFilters(next); runSearch(next)
  }
  function selectSpecies(species: string) {
    const next = [...filters.filter(f => f.feature !== 'species'), { feature: 'species', operator: 'eq', value: species }]
    setFilters(next); setView('search'); setTab('filters'); setMobileTree(false); runSearch(next)
  }
  function exportCsv() {
    const rows = [['group', 'accession', 'species', 'strain'], ...results.confirmed.map(s => [T('明确符合'), s.accession, s.species, s.strain_name]), ...results.possible.map(s => [T('可能符合'), s.accession, s.species, s.strain_name])]
    const blob = new Blob(['\ufeff' + rows.map(r => r.map(x => `"${String(x).replaceAll('"', '""')}"`).join(',')).join('\n')], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = 'microbial-search.csv'; a.click(); URL.revokeObjectURL(url)
  }
  async function interpretNatural() {
    setLoading(true); setError('')
    try { const data = await api<any>('/query/interpret', { method: 'POST', body: JSON.stringify({ text: naturalText }) }); setParsed(data); setFilters(data.filters) } catch (e) { setError(T((e as Error).message)) } finally { setLoading(false) }
  }
  async function runSequence() {
    if (!sequenceFile) { setError(T('请先选择 FASTA 文件')); return }
    setLoading(true); setError(''); setSequenceResult(null)
    const body = new FormData(); body.append('file', sequenceFile); body.append('library', selectedLibrary)
    try { setSequenceResult(await api('/sequence/search', { method: 'POST', body })) } catch (e) { setError(T((e as Error).message)) } finally { setLoading(false) }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="flex items-center gap-3">
          <button className="icon-button mobile-only" onClick={() => setMobileTree(true)} aria-label={T('打开分类树')}><Menu size={20} /></button>
          <div className="brand-mark"><Microscope size={22} /></div>
          <div><h1 className="brand-title">{T('微生物信息查询平台')}</h1><p className="brand-subtitle">{T('序列证据 × 表型筛选 × 文献溯源')}</p></div>
        </div>
        <nav className="topnav">
          <button className={view === 'search' ? 'active' : ''} onClick={() => setView('search')}><Search size={16} />{T('查询工作台')}</button>
          <button className={view === 'literature' ? 'active' : ''} onClick={() => setView('literature')}><BookOpen size={16} />{T('证据文献库')}</button>
        </nav>
        <div className="flex items-center gap-3">
          <div className="health-pill">{health ? (lang === 'en' ? `${health.strains} strains · ${health.species} species · ${health.literature} references` : `${health.strains} 株 · ${health.species} 物种 · ${health.literature} 条文献`) : T('连接中')}</div>
          <button className="language-button" onClick={toggleLang} aria-label="Switch language"><Languages size={16} />{lang === 'en' ? '中文' : 'English'}</button>
        </div>
      </header>

      <div className="demo-banner"><Info size={16} /><span><strong>{T('技术演示：')}</strong>{T('基因组与 ANI 检索使用真实数据；表型为合成演示值，不能用于科研判断。未配置本地千问时，自然语言使用受控规则解析。')}</span></div>

      <div className="workspace">
        {mobileTree && <button className="drawer-backdrop lg:hidden" onClick={() => setMobileTree(false)} aria-label={T('关闭分类树')} />}
        <aside className={`taxonomy-panel ${mobileTree ? 'mobile-open' : ''}`}>
          <div className="panel-heading"><span><Database size={16} />{T('分类浏览')}</span><button className="icon-button mobile-only" onClick={() => setMobileTree(false)} aria-label={T('关闭分类树')}><X size={18} /></button></div>
          <div className="taxonomy-scroll">{tree && <TaxonNode node={tree} depth={0} selected={String(filters.find(f => f.feature === 'species')?.value || '')} onSelect={selectSpecies} t={T} />}</div>
          <div className="index-note"><Info size={14} /><span>{T('索引版本')}<br /><code>{health?.version || T('加载中')}</code></span></div>
        </aside>

        <main className="main-panel">
          {view === 'search' ? (
            <>
              <div className="query-tabs">
                <button className={tab === 'filters' ? 'active' : ''} onClick={() => setTab('filters')}><FlaskConical size={17} />{T('条件筛选')}</button>
                <button className={tab === 'natural' ? 'active' : ''} onClick={() => setTab('natural')}><FileText size={17} />{T('自然语言')}</button>
                <button className={tab === 'sequence' ? 'active' : ''} onClick={() => setTab('sequence')}><Dna size={17} />{T('序列近邻')}</button>
              </div>

              <section className="query-card">
                {tab === 'filters' && <>
                  <div className="section-title"><div><h2>{T('组合条件查询')}</h2><p>{T('所有条件均有记录支持才进入“明确符合”；缺失值进入“可能符合”。')}</p></div></div>
                  <div className="filter-builder">
                    <select value={newFeature} onChange={e => { const f = features.find(x => x.key === e.target.value); setNewFeature(e.target.value); setNewValue(f?.options?.[0] || ''); setNewOperator('eq') }} aria-label={T('筛选字段')}>
                      {features.map(f => <option key={f.key} value={f.key}>{T(f.label)}</option>)}
                    </select>
                    <select value={newOperator} onChange={e => setNewOperator(e.target.value)} aria-label={T('操作符')}>
                      <option value="eq">{T('等于')}</option><option value="contains">{T('包含')}</option><option value="gte">≥</option><option value="lte">≤</option><option value="gt">＞</option><option value="lt">＜</option>
                    </select>
                    {currentFeature?.options?.length ? <select value={newValue} onChange={e => setNewValue(e.target.value)} aria-label={T('筛选值')}>{currentFeature.options.map(v => <option key={v} value={v}>{T(displayValue(v))}</option>)}</select> : <input value={newValue} onChange={e => setNewValue(e.target.value)} placeholder={currentFeature?.type === 'number' ? T('数值') : T('输入值')} aria-label={T('筛选值')} />}
                    <button className="primary-button" onClick={addFilter}><Plus size={16} />{T('添加条件')}</button>
                  </div>
                  <div className="filter-chips">
                    {filters.length === 0 && <span className="text-sm text-slate-500">{T('当前显示全部菌株')}</span>}
                    {filters.map((f, i) => <span className="filter-chip" key={`${f.feature}-${i}`}>{T(label(f.feature))} {f.operator === 'eq' ? '＝' : f.operator === 'contains' ? T('包含') : f.operator} {T(displayValue(f.value))}{f.unit && f.unit !== '%' ? f.unit : f.unit}<button onClick={() => { const next = filters.filter((_, j) => j !== i); setFilters(next); runSearch(next) }} aria-label={T('删除条件')}><X size={13} /></button></span>)}
                  </div>
                </>}

                {tab === 'natural' && <>
                  <div className="section-title"><div><h2>{T('描述你的查询需求')}</h2><p>{T('先显示系统理解的条件，再由你确认执行，不直接生成 SQL。')}</p></div></div>
                  <textarea className="natural-input" rows={3} value={naturalText} onChange={e => setNaturalText(e.target.value)} />
                  <div className="flex flex-wrap gap-2 mt-3">
                    <button className="primary-button" onClick={interpretNatural} disabled={loading}><Search size={16} />{T('解析查询')}</button>
                    {['找一些耐盐的海洋厌氧菌', '不运动的短双歧杆菌', '耐盐≥3%的大肠杆菌'].map(x => <button className="secondary-button" key={x} onClick={() => setNaturalText(lang === 'en' ? T(x) : x)}>{T(x)}</button>)}
                  </div>
                  {parsed && <div className="parse-result">
                    <div className="text-sm font-medium text-slate-700 mb-2">{T('系统理解：')}</div>
                    <div className="filter-chips">{parsed.filters.map((f: Filter, i: number) => <span className="filter-chip" key={i}>{T(label(f.feature))}: {T(displayValue(f.value))}{f.unit}</span>)}</div>
                    {parsed.warnings.map((w: string, i: number) => <div className="warning-line" key={i}><AlertTriangle size={15} />{T(w)}</div>)}
                    <div className="flex flex-wrap gap-2 mt-3">
                      <button className="primary-button" disabled={!parsed.filters.length} onClick={() => runSearch(parsed.filters)}><CheckCircle2 size={16} />{T('按明确条件查询')}</button>
                      {naturalText.includes('耐盐') && <button className="secondary-button" onClick={() => { const next = [...parsed.filters, { feature: 'salt_tolerance_description', operator: 'eq', value: 'true', unit: '' }]; setFilters(next); runSearch(next) }}>{T('添加“资料明确耐盐”条件')}</button>}
                    </div>
                  </div>}
                </>}

                {tab === 'sequence' && <>
                  <div className="section-title"><div><h2>{T('上传 FASTA，查找库内近邻')}</h2><p>{T('服务器使用 skani ANI；本地无 skani 时明确降级为 k-mer Jaccard，二者不混用。')}</p></div></div>
                  <div className="mb-4">
                    <select value={selectedLibrary} onChange={e => setSelectedLibrary(e.target.value)} aria-label={T('参考基因库')}>
                      <option value="demo">{T('演示参考库（12 株）')}</option>
                      <option value="four_species" disabled={!libraryStatus?.all_index_ready}>{T('四物种完整库')}{libraryStatus ? ` (${libraryStatus.total_expected_files.toLocaleString()} ${lang === 'en' ? 'strains' : '株'}${T(libraryStatus.all_index_ready ? '，索引就绪' : '，索引构建中')})` : ''}</option>
                    </select>
                    {libraryStatus && !libraryStatus.all_index_ready && <p className="text-xs text-slate-500 mt-2">{T('大文件已保存在服务器，传输完成不等于索引就绪；索引进度不影响现有 12 株演示查询。')}</p>}
                  </div>
                  <label className="upload-zone">
                    <input type="file" accept=".fa,.fna,.fasta,.gz" onChange={e => setSequenceFile(e.target.files?.[0] || null)} />
                    <Upload size={28} /><strong>{sequenceFile ? sequenceFile.name : T('选择 FASTA 文件')}</strong><span>{T('完整／草图基因组，支持 gzip，最大 50 MB')}</span>
                  </label>
                  <button className="primary-button mt-4" onClick={runSequence} disabled={loading}>{loading ? <Loader2 className="animate-spin" size={16} /> : <Dna size={16} />}{T('开始近邻检索')}</button>
                  {sequenceResult && <div className="sequence-result">
                    <div className={`evidence-banner ${sequenceResult.evidence_level}`}><Info size={17} /><div><strong>{T(sequenceResult.evidence_level === 'high_neighbor' ? '库内高度近邻' : sequenceResult.evidence_level === 'insufficient' ? '证据不足' : '当前库内最近')}</strong><p>{T(sequenceResult.message)}</p></div></div>
                    <div className="text-sm text-slate-500 mb-3">{T('方法：')}{sequenceResult.method} · {sequenceResult.sequences} {T('条序列')} · {sequenceResult.bases.toLocaleString()} bp</div>
                    {sequenceResult.matches.map((match: SequenceMatch, i: number) => <button className="match-row" key={match.strain.id} onClick={() => setSelectedStrain(match.strain.id)}>
                      <span className="match-rank">#{i + 1}</span><span className="match-name"><strong>{match.strain.strain_name}</strong><em>{match.strain.species}</em></span><span className="match-score">{match.score.toFixed(2)}<small>{match.score_type}</small></span><ChevronRight size={16} />
                    </button>)}
                  </div>}
                </>}
              </section>

              {error && <div className="error-banner"><AlertTriangle size={17} />{T(error)}</div>}

              <section className="results-section">
                <div className="results-header"><div><h2>{T('查询结果')}</h2><span>{T('明确符合')} {results.counts.confirmed} · {T('可能符合')} {results.counts.possible}</span></div><button className="secondary-button" onClick={exportCsv}><Download size={16} />{T('导出 CSV')}</button></div>
                {loading && <div className="loading-line"><Loader2 className="animate-spin" size={18} />{T('正在查询')}</div>}
                <h3 className="result-group-title"><CheckCircle2 size={17} />{T('明确符合')} <span>{results.confirmed.length}</span></h3>
                {results.confirmed.length ? <ResultTable items={results.confirmed} onSelect={setSelectedStrain} t={T} /> : <div className="empty-state">{T('没有所有条件均明确支持的菌株。')}</div>}
                {results.possible.length > 0 && <><h3 className="result-group-title possible"><Info size={17} />{T('可能符合')} <span>{results.possible.length}</span></h3><ResultTable items={results.possible} onSelect={setSelectedStrain} t={T} /></>}
              </section>
            </>
          ) : (
            <section className="literature-section">
              <div className="section-title"><div><h2>{T('证据文献库')}</h2><p>{T('核心文献与分享线索分级保存；未核对原文的内容不直接支撑性状结论。')}</p></div></div>
              <div className="literature-toolbar">
                <div className="segmented"><button className={literatureType === 'core' ? 'active' : ''} onClick={() => setLiteratureType('core')}>{T('核心文献')}</button><button className={literatureType === 'share_lead' ? 'active' : ''} onClick={() => setLiteratureType('share_lead')}>{T('分享线索')}</button></div>
                <input value={literatureQuery} onChange={e => setLiteratureQuery(e.target.value)} onKeyDown={e => { if (e.key === 'Enter') loadLiterature() }} placeholder={T('搜索题目、作者或项目关系')} />
                <button className="primary-button" onClick={() => loadLiterature()}><Search size={16} />{T('检索')}</button>
              </div>
              {literatureType === 'share_lead' && <div className="warning-line mb-4"><AlertTriangle size={16} />{T('这些条目可能是解读、新闻或重复分享，标题和原文链接仍需逐条核对。')}</div>}
              <div className="literature-list">{literature.map(item => <article className="literature-item" key={item.id}>
                <div className="literature-meta"><span>{item.record_type === 'core' ? item.journal : `${T('原编号')} ${item.original_number}`}</span><span>{item.record_type === 'core' ? item.year : item.shared_date}</span><span className="verification">{T(item.verification_status)}</span></div>
                <h3>{item.title}</h3><p>{item.authors}</p><div className="project-relation">{T(item.project_relation)}</div>
                {item.related_strains.length > 0 && <div className="related-strains">{T('关联菌株：')}{item.related_strains.map(id => <button key={id} onClick={() => setSelectedStrain(id)}>{id}</button>)}</div>}
              </article>)}</div>
            </section>
          )}
        </main>
      </div>

      {selectedStrain && <>
        <button className="drawer-backdrop" onClick={() => setSelectedStrain(null)} aria-label={T('关闭菌株详情')} />
        <aside className="detail-panel" role="dialog" aria-modal="true" aria-label={T('菌株详情')}>
          <div className="detail-header"><div><span className="eyebrow">{T('菌株详情')}</span><h2>{selectedStrainData?.strain_name || selectedStrain}</h2><p className="italic">{selectedStrainData?.species}</p></div><button className="icon-button" onClick={() => setSelectedStrain(null)} aria-label={T('关闭菌株详情')}><X size={20} /></button></div>
          <div className="detail-body">
            <div className="detail-grid"><div><span>Accession</span><strong>{selectedStrain}</strong></div><div><span>{T('内部编号')}</span><strong>{selectedStrainData?.internal_id || '—'}</strong></div><div><span>{T('模式菌株')}</span><strong>{selectedStrainData?.type_strain === 'unknown' ? T('未知') : selectedStrainData?.type_strain || T('未知')}</strong></div><div><span>{T('基因组')}</span><strong>{T('真实序列')}</strong></div></div>
            <div className="lineage-box"><span>{T('分类路径')}</span><p>{selectedStrainData?.lineage_json ? JSON.parse(selectedStrainData.lineage_json).join(' › ') : selectedStrainData?.species}</p></div>
            <div className="warning-line"><AlertTriangle size={15} />{T('以下性状均为合成演示值，仅用于验证查询与证据展示。')}</div>
            <h3 className="detail-section-title">{T('性状观察与来源')}</h3>
            <div className="observation-list">{observations.map(obs => <div className="observation-row" key={obs.id}><div><span className="obs-feature">{T(label(obs.feature))}</span><strong>{T(displayValue(obs.value))}{obs.unit && obs.unit !== 'pH' ? ` ${obs.unit}` : obs.unit}</strong></div><p>{T(obs.condition_text)}</p><span className="demo-source">{T(obs.evidence?.title || '演示来源')}</span></div>)}</div>
          </div>
        </aside>
      </>}
    </div>
  )
}
