// Match page — three tabs, upload, results

const API_BASE = 'http://localhost:8000';
const MODEL_NAME = 'BAAI/bge-large-en-v1.5';

const SCRAPE_SITES = [
  { id: 'indeed',        label: 'Indeed' },
  { id: 'glassdoor',     label: 'Glassdoor' },
  { id: 'zip_recruiter', label: 'ZipRecruiter' },
  { id: 'google',        label: 'Google Jobs' },
];
const SITE_LABEL = Object.fromEntries(SCRAPE_SITES.map(s => [s.id, s.label]));

// ── API helpers ───────────────────────────────────────────────────────────────

function formatDetail(detail, status) {
  if (!detail) return `HTTP ${status}`;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail
      .map(d => (d && d.msg)
        ? `${d.msg}${d.loc ? ` (${d.loc.slice(-1)})` : ''}`
        : (typeof d === 'string' ? d : JSON.stringify(d)))
      .join('; ');
  }
  return typeof detail === 'object' ? JSON.stringify(detail) : String(detail);
}

async function apiMatch(endpoint, body) {
  const res = await fetch(`${API_BASE}/api/match/${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(formatDetail(err.detail, res.status));
  }
  return res.json();
}

async function apiFeedback(evalId, resultId, action) {
  // Best-effort: silently swallow errors so a feedback failure never breaks the UI.
  try {
    await fetch(`${API_BASE}/api/eval/feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ eval_id: evalId, result_id: resultId, action }),
    });
  } catch (_) {}
}

async function apiScrapeJobs(text, sites = ['indeed']) {
  // Smaller per-site batch when several sources are selected, to keep total
  // scrape time roughly bounded (~30-60s).
  const per_site = sites.length <= 1 ? 25 : sites.length === 2 ? 20 : 15;
  const res = await fetch(`${API_BASE}/api/scrape/jobs-for-query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, location: 'remote', results_wanted: per_site, sites }),
  });
  const json = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(formatDetail(json.detail, res.status));
  return json;
}

// ── Result normalisers ────────────────────────────────────────────────────────

function sourceBadge(source) {
  // Map raw DB `source` to a short, friendly display label.
  if (!source) return null;
  const s = String(source);
  if (s.startsWith('jobspy:')) {
    const site = s.slice('jobspy:'.length);
    return site.charAt(0).toUpperCase() + site.slice(1).replace('_', ' ');
  }
  if (s === 'user_submission')          return 'User';
  if (s === 'JOB_data_sample.csv')      return 'Sample';
  if (s.startsWith('sid1877'))          return 'Sample';
  return s.length > 14 ? s.slice(0, 14) + '…' : s;
}

function normalizeJob(r) {
  return {
    id:         r.job_id,
    score:      r.similarity,
    title:      r.title      || 'Untitled Role',
    company:    r.company    || '—',
    location:   r.work_type  || '—',
    type:       r.work_type  || '—',
    salary:     r.salary     || 'Not specified',
    experience: r.experience || 'Not specified',
    edu:        '—',
    matched:    r.matched_skills || [],
    missing:    r.missing_skills || [],
    source:     sourceBadge(r.source),
    jobUrl:     r.job_url || null,
    companyUrl: r.company_url || null,
  };
}

function normalizeResume(r) {
  return {
    id:         r.resume_id,
    score:      r.similarity,
    title:      r.category   || 'Candidate',
    company:    'Resume',
    location:   '—',
    type:       '—',
    salary:     '—',
    experience: '—',
    edu:        '—',
    matched:    r.matched_skills || [],
    missing:    r.missing_skills || [],
    preview:    r.preview,
    source:     sourceBadge(r.source),
  };
}

// ── Components ────────────────────────────────────────────────────────────────

function UploadZone({ file, onPick, onClear, label = 'resume' }) {
  const [drag, setDrag] = React.useState(false);
  const inputRef = React.useRef(null);
  const handlePick = () => inputRef.current?.click();

  const readFile = (f) => {
    if (!f) return;
    const reader = new FileReader();
    reader.onload = (e) => onPick({ name: f.name, size: f.size, content: e.target.result });
    // Read as text — works for .txt; PDF/DOCX will look garbled but user can paste instead
    reader.readAsText(f);
  };

  if (file) {
    return (
      <div className="upload-zone has-file">
        <div className="upload-file">
          <div className="upload-file-meta">
            <div className="upload-icon" style={{margin: 0, width: 28, height: 28}}>
              <Icon.Doc size={14}/>
            </div>
            <div>
              <div className="upload-file-name">{file.name}</div>
              <div className="upload-file-size">{(file.size/1024).toFixed(1)} KB · {file.content ? 'Ready' : 'Parsed'}</div>
            </div>
          </div>
          <button className="icon-btn" onClick={onClear} title="Remove">
            <Icon.X />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`upload-zone ${drag?'drag':''}`}
      onClick={handlePick}
      onDragOver={(e)=>{e.preventDefault(); setDrag(true);}}
      onDragLeave={()=>setDrag(false)}
      onDrop={(e)=>{
        e.preventDefault(); setDrag(false);
        const f = e.dataTransfer?.files?.[0];
        if (f) readFile(f);
      }}
    >
      <div className="upload-icon"><Icon.Upload /></div>
      <div className="upload-title">Drop your {label} here</div>
      <div className="upload-hint">PDF, DOCX, or TXT — up to 5MB</div>
      <input ref={inputRef} type="file" hidden accept=".pdf,.docx,.txt"
        onChange={(e) => readFile(e.target.files?.[0])}/>
    </div>
  );
}

function TopKSelect({ value, onChange }) {
  return (
    <label className="select-wrap">
      <span className="label">Top K</span>
      <select className="select" value={value} onChange={(e)=>onChange(+e.target.value)}>
        {[3,5,10,20].map(n => <option key={n} value={n}>{n} results</option>)}
      </select>
    </label>
  );
}

function SkeletonCard() {
  return (
    <div className="skel">
      <div style={{display:'flex', justifyContent:'space-between', gap: 12, marginBottom: 12}}>
        <div className="skel-line" style={{width: '46%'}}/>
        <div className="skel-line" style={{width: 40, height: 16, borderRadius: 999}}/>
      </div>
      <div className="skel-line" style={{width: '70%', height: 8, marginBottom: 14}}/>
      <div className="skel-line" style={{width: '100%', height: 4, marginBottom: 14}}/>
      <div style={{display:'flex', gap: 6}}>
        <div className="skel-line" style={{width: 60, height: 18, borderRadius: 999}}/>
        <div className="skel-line" style={{width: 80, height: 18, borderRadius: 999}}/>
        <div className="skel-line" style={{width: 70, height: 18, borderRadius: 999}}/>
        <div className="skel-line" style={{width: 50, height: 18, borderRadius: 999}}/>
      </div>
    </div>
  );
}

function ResultCard({ item, mode, feedback, onFeedback }) {
  const isResume = mode === 'j2r';

  return (
    <div className="result-card">
      <div className="result-top">
        <div style={{minWidth: 0}}>
          <div style={{display:'flex', alignItems:'center', gap: 8, flexWrap:'wrap'}}>
            <h3 className="result-title" style={{margin: 0}}>
              {item.jobUrl ? (
                <a href={item.jobUrl} target="_blank" rel="noreferrer noopener"
                   style={{color:'inherit', textDecoration:'none'}}
                   onMouseEnter={(e)=>e.currentTarget.style.textDecoration='underline'}
                   onMouseLeave={(e)=>e.currentTarget.style.textDecoration='none'}>
                  {item.title} <Icon.Arrow size={11}/>
                </a>
              ) : item.title}
            </h3>
            {item.source && (
              <span style={{
                fontSize: 10, fontWeight: 500, textTransform:'uppercase',
                letterSpacing: 0.3, padding:'2px 6px', borderRadius: 4,
                background:'var(--bg-soft)', color:'var(--ink-500)',
                border:'0.5px solid var(--border)'
              }}>
                {item.source}
              </span>
            )}
          </div>
          {isResume ? (
            <div className="result-meta">
              <span>Resume · {item.title} specialist</span>
            </div>
          ) : (
            <div className="result-meta">
              {item.companyUrl ? (
                <a href={item.companyUrl} target="_blank" rel="noreferrer noopener"
                   style={{color:'inherit'}}>{item.company}</a>
              ) : (
                <span>{item.company}</span>
              )}
              <span className="result-meta-dot"/>
              <span>{item.location}</span>
            </div>
          )}
        </div>
        <ScoreBadge value={item.score} />
      </div>
      <ScoreBar value={item.score} />

      {!isResume && (
        <div className="result-attrs">
          <span className="result-attr">
            <span className="result-attr-icon"><Icon.MoneyDot/></span>
            {item.salary}
          </span>
          <span className="result-attr">
            <span className="result-attr-icon"><Icon.Briefcase size={12}/></span>
            {item.experience}
          </span>
          <span className="result-attr">
            <span className="result-attr-icon"><Icon.Cap/></span>
            {item.type}
          </span>
        </div>
      )}

      <div className="pills">
        {item.matched.map(s => <Pill key={s}>{s}</Pill>)}
        {item.missing.map(s => <Pill key={s} miss>{s}</Pill>)}
      </div>

      <div className="result-foot" style={{display:'flex', justifyContent:'flex-end', marginTop: 10}}>
        <Feedback value={feedback} onChange={onFeedback} />
      </div>
    </div>
  );
}

function EmptyState({ mode, error }) {
  if (error) return (
    <div style={{padding:'60px 20px', textAlign:'center'}}>
      <div style={{
        width: 48, height: 48, borderRadius: 12,
        background:'#FEF2F2', margin:'0 auto 16px',
        display:'grid', placeItems:'center', color:'#EF4444'
      }}>⚠</div>
      <div style={{fontWeight: 500, color:'var(--ink-900)', marginBottom: 4}}>API error</div>
      <div style={{fontSize: 12, color:'var(--ink-500)', maxWidth: 320, margin:'0 auto'}}>{error}</div>
    </div>
  );
  return (
    <div style={{padding:'60px 20px', textAlign:'center', color:'var(--ink-500)', fontSize: 13}}>
      <div style={{
        width: 48, height: 48, borderRadius: 12,
        background:'var(--bg-soft)', margin:'0 auto 16px',
        display:'grid', placeItems:'center', color:'var(--ink-400)'
      }}>
        <Icon.Search size={20}/>
      </div>
      <div style={{fontWeight: 500, color:'var(--ink-700)', marginBottom: 4}}>No matches yet</div>
      <div>Upload or paste {mode === 'r2j' ? 'a resume' : 'a job description'} and click <span className="kbd">Find matches</span>.</div>
    </div>
  );
}

// ── Result sorting ───────────────────────────────────────────────────────────

function parseSalary(s) {
  // "$59K-$99K" → 59000; "$210k–260k" → 210000; "$140k-180k" → 140000
  const m = String(s || '').match(/\$?\s*(\d+(?:\.\d+)?)\s*([Kk]?)/);
  if (!m) return -1;
  return parseFloat(m[1]) * (m[2] ? 1000 : 1);
}
function parseExperience(s) {
  // "5 to 15 Years" → 5; "5+ yrs" → 5
  const m = String(s || '').match(/(\d+)/);
  return m ? parseInt(m[1], 10) : -1;
}
function sortResults(items, sort) {
  const copy = [...items];
  switch (sort) {
    case 'salary':
      return copy.sort((a, b) => parseSalary(b.salary) - parseSalary(a.salary));
    case 'experience':
      return copy.sort((a, b) => parseExperience(b.experience) - parseExperience(a.experience));
    case 'work_type':
      return copy.sort((a, b) => String(a.type || '').localeCompare(String(b.type || '')));
    case 'score':
    default:
      return copy.sort((a, b) => b.score - a.score);
  }
}

function ResultsPanel({ loading, results, error, mode, elapsed, onRerun, feedback, setFeedback, evalId, onRefreshFromSources, refreshing, refreshMsg, scrapeSites, toggleScrapeSite }) {
  const [sort, setSort] = React.useState('score');
  const isResume = mode === 'j2r';
  const sorted = results ? sortResults(results, sort) : null;

  const refreshLabel = (() => {
    if (refreshing) return 'Scraping…';
    if (!scrapeSites || scrapeSites.length === 0) return 'Pick a source';
    if (scrapeSites.length === 1) return `Refresh from ${SITE_LABEL[scrapeSites[0]] || scrapeSites[0]}`;
    if (scrapeSites.length === SCRAPE_SITES.length) return `Refresh from all ${SCRAPE_SITES.length} sources`;
    return `Refresh from ${scrapeSites.length} sources`;
  })();

  return (
    <section className="panel" data-screen-label="Results">
      <div className="results-head">
        <div style={{display:'flex', alignItems:'center', gap: 10}}>
          <span className="results-title">Top matches</span>
          {!loading && results && <span className="results-count">{results.length} results</span>}
          {!loading && elapsed && <span className="tiny muted">{elapsed}ms</span>}
        </div>
        <div className="results-actions">
          {!loading && results && results.length > 0 && (
            <>
              <select
                className="select"
                style={{height: 26, fontSize: 12, padding:'0 8px'}}
                value={sort}
                onChange={(e)=>setSort(e.target.value)}
                title="Sort by"
              >
                <option value="score">Sort: Score</option>
                {!isResume && <option value="salary">Sort: Salary</option>}
                {!isResume && <option value="experience">Sort: Experience</option>}
                {!isResume && <option value="work_type">Sort: Work type</option>}
              </select>
              {!isResume && onRefreshFromSources && (
                <button
                  className="btn btn-naked"
                  style={{height: 26, fontSize: 12}}
                  onClick={onRefreshFromSources}
                  disabled={refreshing || !scrapeSites || scrapeSites.length === 0}
                  title="Scrape selected job sources for fresh postings matching this resume"
                >
                  {refreshLabel}
                </button>
              )}
              <button className="btn btn-naked" style={{height: 26, fontSize: 12}} onClick={onRerun}>
                Re-run
              </button>
            </>
          )}
        </div>
      </div>
      {!isResume && !loading && results && results.length > 0 && scrapeSites && toggleScrapeSite && (
        <div style={{
          display:'flex', alignItems:'center', gap: 6, flexWrap:'wrap',
          padding:'8px 16px 0', fontSize: 11, color:'var(--ink-500)',
        }}>
          <span style={{marginRight: 4}}>Sources:</span>
          {SCRAPE_SITES.map(s => {
            const active = scrapeSites.includes(s.id);
            return (
              <button
                key={s.id}
                onClick={() => toggleScrapeSite(s.id)}
                disabled={refreshing}
                style={{
                  height: 22, fontSize: 11, padding:'0 10px', borderRadius: 999,
                  border: '0.5px solid var(--border)',
                  background: active ? 'var(--purple-100)' : 'transparent',
                  color: active ? 'var(--purple-700)' : 'var(--ink-500)',
                  fontWeight: active ? 500 : 400,
                  cursor: refreshing ? 'not-allowed' : 'pointer',
                  opacity: refreshing ? 0.6 : 1,
                }}
              >
                {s.label}
              </button>
            );
          })}
        </div>
      )}
      {refreshMsg && (
        <div style={{
          margin:'8px 16px 0', padding:'8px 12px', borderRadius: 6, fontSize: 12,
          background: refreshMsg.ok ? '#ECFDF5' : '#FEF2F2',
          color:      refreshMsg.ok ? '#047857' : '#EF4444',
        }}>
          {refreshMsg.ok ? '✓ ' : '⚠ '}{refreshMsg.msg}
        </div>
      )}
      <div className="results-list">
        {loading && [0,1,2,3,4].map(i => <SkeletonCard key={i}/>)}
        {!loading && !results && <EmptyState mode={mode} error={error} />}
        {!loading && results && results.length === 0 && (
          <div style={{padding:'60px 20px', textAlign:'center', color:'var(--ink-500)', fontSize: 13}}>
            <div style={{marginBottom: 8}}>No results yet — the database may still be populating.</div>
            <div className="tiny muted">Migration runs in the background. Try again in a few minutes.</div>
          </div>
        )}
        {!loading && sorted && sorted.map(item => (
          <ResultCard
            key={item.id}
            item={item}
            mode={mode}
            feedback={feedback[item.id]}
            onFeedback={(v) => {
              setFeedback(prev => ({ ...prev, [item.id]: v }));
              if (evalId && v) apiFeedback(evalId, item.id, v);
            }}
          />
        ))}
      </div>
    </section>
  );
}

function InputPanel({ mode, setMode, text, setText, file, setFile, topK, setTopK, onSubmit, busy }) {
  const isOO = mode === 'oo';
  return (
    <section className="panel" data-screen-label="Input">
      <div className="tabs" role="tablist">
        <button className={`tab ${mode==='r2j'?'active':''}`} onClick={()=>setMode('r2j')} role="tab">
          <Icon.Doc size={13}/> Resume → Jobs
        </button>
        <button className={`tab ${mode==='j2r'?'active':''}`} onClick={()=>setMode('j2r')} role="tab">
          <Icon.Briefcase size={13}/> Job → Resumes
        </button>
        <button className={`tab ${mode==='oo'?'active':''}`} onClick={()=>setMode('oo')} role="tab">
          <Icon.Swap size={13}/> One-to-one
        </button>
      </div>
      <div className="panel-pad">
        {!isOO && (
          <>
            <UploadZone
              file={file}
              onPick={(f) => { setFile(f); if (f.content) setText(f.content); }}
              onClear={()=>{ setFile(null); }}
              label={mode==='r2j' ? 'resume' : 'job description'}
            />
            <div className="divider-or">or paste text</div>
            <textarea
              className="textarea"
              placeholder={mode==='r2j' ? 'Paste resume text…' : 'Paste job description…'}
              value={text}
              onChange={(e)=>setText(e.target.value)}
            />
            <div style={{marginTop: 8}}>
              <button className="link-btn" onClick={()=>setText(mode==='r2j' ? SAMPLE_RESUME : SAMPLE_JD)}>
                Use sample {mode==='r2j' ? 'resume' : 'job description'}
              </button>
            </div>
            <div className="input-row">
              <TopKSelect value={topK} onChange={setTopK}/>
              <button
                className="btn btn-primary"
                style={{height: 32, alignSelf: 'end'}}
                disabled={(!text && !file) || busy}
                onClick={onSubmit}
              >
                {busy ? 'Matching…' : <React.Fragment>Find matches <Icon.Arrow /></React.Fragment>}
              </button>
            </div>
          </>
        )}
        {isOO && <OneToOnePanel />}
      </div>
    </section>
  );
}

function OneToOnePanel() {
  const [jd, setJd] = React.useState(SAMPLE_JD);
  const [resume, setResume] = React.useState(SAMPLE_RESUME);
  const [result, setResult] = React.useState(null);
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState(null);

  const compute = async () => {
    setBusy(true);
    setResult(null);
    setError(null);
    try {
      const data = await apiMatch('one-to-one', {
        job_text: jd,
        resume_text: resume,
        model_name: MODEL_NAME,
      });
      setResult({
        score:   data.similarity,
        matched: data.matched_skills,
        missing: data.job_skills.filter(s => !data.matched_skills.includes(s)),
        quality: data.quality,
      });
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const tier = result ? tierFor(result.score) : null;

  return (
    <div>
      <div className="oo-grid">
        <div className="oo-textarea-wrap">
          <span className="label"><Icon.Briefcase size={11}/> Job description</span>
          <textarea
            className="textarea"
            style={{minHeight: 220}}
            value={jd}
            onChange={(e)=>setJd(e.target.value)}
            placeholder="Paste job description…"
          />
        </div>
        <div className="oo-textarea-wrap">
          <span className="label"><Icon.Doc size={11}/> Resume</span>
          <textarea
            className="textarea"
            style={{minHeight: 220}}
            value={resume}
            onChange={(e)=>setResume(e.target.value)}
            placeholder="Paste resume text…"
          />
        </div>
      </div>
      <div style={{display:'flex', justifyContent:'flex-end', alignItems:'flex-end', marginTop: 16, gap: 12}}>
        <button
          className="btn btn-primary"
          style={{height: 32}}
          onClick={compute}
          disabled={busy || !jd || !resume}
        >
          {busy ? 'Computing…' : <React.Fragment><Icon.Swap size={13}/> Compute similarity</React.Fragment>}
        </button>
      </div>

      {error && (
        <div style={{marginTop: 16, padding:'12px 16px', background:'#FEF2F2', borderRadius: 8, fontSize: 12, color:'#EF4444'}}>
          {error}
        </div>
      )}

      {busy && (
        <div className="score-display" style={{borderTop: '0.5px solid var(--border)', marginTop: 20}}>
          <div className="skel-line" style={{height: 48, width: 140, margin: '0 auto', borderRadius: 8}}/>
          <div className="skel-line" style={{height: 10, width: 100, margin: '14px auto 0', borderRadius: 6}}/>
          <div className="skel-line" style={{height: 6, width: '70%', margin: '20px auto 0'}}/>
        </div>
      )}

      {result && !busy && (
        <div className="score-display" style={{borderTop: '0.5px solid var(--border)', marginTop: 20}}>
          <div className={`score-big ${tier}`}>{(result.score*100).toFixed(1)}%</div>
          <div className="score-label">cosine similarity</div>
          <div className="score-quality">{result.quality} match</div>
          <div style={{maxWidth: 380, margin: '0 auto'}}>
            <ScoreBar value={result.score} large />
          </div>
          <div style={{marginTop: 20, display:'flex', flexDirection:'column', gap: 10, alignItems:'center'}}>
            <div style={{fontSize: 11, color:'var(--ink-500)', textTransform:'uppercase', letterSpacing:'0.06em'}}>
              {result.matched.length} matched · {result.missing.length} gaps
            </div>
            <div className="pills" style={{justifyContent:'center', maxWidth: 540}}>
              {result.matched.map(s => <Pill key={s}>{s}</Pill>)}
              {result.missing.map(s => <Pill key={s} miss>{s}</Pill>)}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function MatchPage() {
  const [mode, setMode] = React.useState('r2j');
  const [text, setText] = React.useState(SAMPLE_RESUME);
  const [file, setFile] = React.useState(null);
  const [topK, setTopK] = React.useState(5);
  const [results, setResults] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState(null);
  const [elapsed, setElapsed] = React.useState(null);
  const [evalId, setEvalId] = React.useState(null);
  const [feedback, setFeedback] = React.useState({});
  const [refreshing, setRefreshing] = React.useState(false);
  const [refreshMsg, setRefreshMsg] = React.useState(null);
  const [scrapeSites, setScrapeSites] = React.useState(['indeed']);

  // Reset when switching tabs
  React.useEffect(() => {
    setResults(null);
    setError(null);
    setElapsed(null);
    setEvalId(null);
    setFeedback({});
    setRefreshMsg(null);
    if (mode === 'r2j') setText(SAMPLE_RESUME);
    if (mode === 'j2r') setText(SAMPLE_JD);
  }, [mode]);

  const submit = async () => {
    const queryText = file?.content || text;
    if (!queryText?.trim()) return;

    setLoading(true);
    setResults(null);
    setError(null);
    setEvalId(null);
    setFeedback({});

    try {
      const endpoint = mode === 'r2j' ? 'resume-jobs' : 'job-resumes';
      const data = await apiMatch(endpoint, {
        text:       queryText,
        model_name: MODEL_NAME,
        top_k:      topK,
        rerank:     true,
      });

      const normalize = mode === 'r2j' ? normalizeJob : normalizeResume;
      setResults((data.results || []).map(normalize));
      setElapsed(data.elapsed_ms);
      setEvalId(data.eval_id || null);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const refreshFromSources = async () => {
    const queryText = file?.content || text;
    if (!queryText?.trim() || refreshing || scrapeSites.length === 0) return;
    setRefreshing(true);
    setRefreshMsg(null);
    try {
      const data = await apiScrapeJobs(queryText, scrapeSites);
      const inserted = data.inserted ?? 0;
      const where = scrapeSites.map(s => SITE_LABEL[s] || s).join(', ');
      setRefreshMsg({
        ok: true,
        msg: `Added ${inserted} job${inserted === 1 ? '' : 's'} from ${where} (search: "${data.search_term}"). Refreshing results…`,
      });
      await submit();
    } catch (e) {
      setRefreshMsg({ ok: false, msg: `Scrape failed: ${e.message}` });
    } finally {
      setRefreshing(false);
    }
  };

  const toggleScrapeSite = (id) => {
    setScrapeSites(prev => prev.includes(id) ? prev.filter(s => s !== id) : [...prev, id]);
  };

  return (
    <div className="match-shell" data-screen-label="02 Match">
      <div className="match-head">
        <div>
          <h1 className="match-h">Match</h1>
          <p className="match-sub">
            {mode==='r2j' && 'Surface the best-fit jobs for a candidate.'}
            {mode==='j2r' && 'Surface the best-fit candidates for a role.'}
            {mode==='oo'  && 'Compare a single resume against a single job description.'}
          </p>
        </div>
      </div>

      {mode !== 'oo' ? (
        <div className="match-grid">
          <InputPanel
            mode={mode} setMode={setMode}
            text={text} setText={setText}
            file={file} setFile={setFile}
            topK={topK} setTopK={setTopK}
            onSubmit={submit} busy={loading}
          />
          <ResultsPanel
            loading={loading} results={results} error={error}
            mode={mode} elapsed={elapsed}
            onRerun={submit}
            feedback={feedback} setFeedback={setFeedback}
            evalId={evalId}
            onRefreshFromSources={refreshFromSources}
            refreshing={refreshing}
            refreshMsg={refreshMsg}
            scrapeSites={scrapeSites}
            toggleScrapeSite={toggleScrapeSite}
          />
        </div>
      ) : (
        <InputPanel
          mode={mode} setMode={setMode}
        />
      )}
    </div>
  );
}

Object.assign(window, { MatchPage });
