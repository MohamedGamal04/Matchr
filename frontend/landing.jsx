// Landing page

function Nav({ route, onRoute }) {
  return (
    <header className="nav" data-screen-label="Nav">
      <div className="nav-inner">
        <a className="brand" href="#/" onClick={(e)=>{e.preventDefault(); onRoute('landing');}}>
          <Logo />
          <span className="brand-name">Matchr</span>
        </a>
        <nav className="nav-links">
          <a className={`nav-link ${route==='match'?'active':''}`} href="#/match" onClick={(e)=>{e.preventDefault(); onRoute('match');}}>Match</a>
          <a className={`nav-link ${route==='add'?'active':''}`} href="#/add" onClick={(e)=>{e.preventDefault(); onRoute('add');}}>Add data</a>
          <a className={`nav-link ${route==='metrics'?'active':''}`} href="#/metrics" onClick={(e)=>{e.preventDefault(); onRoute('metrics');}}>Metrics</a>
          <a className="nav-link" href="#how" onClick={(e)=>{e.preventDefault(); onRoute('landing'); setTimeout(()=>document.getElementById('how')?.scrollIntoView({behavior:'smooth', block:'start'}), 10);}}>How it works</a>
        </nav>
        <div className="nav-right">
          <button className="btn btn-primary" onClick={()=>onRoute('match')}>Get started</button>
        </div>
      </div>
    </header>
  );
}

function Hero({ onRoute }) {
  return (
    <section className="hero" data-screen-label="Hero">
      <span className="pill-badge"><Icon.Sparkle /> Semantic NLP matching</span>
      <h1 className="h1">Find the right match,<br/>in seconds.</h1>
      <p className="subtitle">
        Upload a resume or job description and let transformer models surface the most relevant matches with similarity scores and skill overlap.
      </p>
      <div className="hero-ctas">
        <button className="btn btn-primary btn-lg" onClick={()=>onRoute('match')}>
          Try it free <Icon.Arrow />
        </button>
      </div>
      <div className="stat-bar">
        <div className="stat">
          <span className="stat-num">1</span>
          <span className="stat-label">Embedding model</span>
        </div>
        <div className="stat">
          <span className="stat-num">PDF · DOCX · TXT</span>
          <span className="stat-label">Supported formats</span>
        </div>
        <div className="stat">
          <span className="stat-num">&lt; 2s</span>
          <span className="stat-label">Avg. match time</span>
        </div>
      </div>
    </section>
  );
}

function HeroPreview() {
  // Compact, non-interactive preview of the match screen
  return (
    <section className="section" style={{paddingTop: 0, paddingBottom: 56}}>
      <div className="demo-frame">
        <div className="demo-frame-bar">
          <span className="dot"/><span className="dot"/><span className="dot"/>
          <span className="demo-frame-url">matchr.ai/match</span>
        </div>
        <div style={{display:'grid', gridTemplateColumns:'4fr 6fr', gap: 0}}>
          <div style={{padding: 20, borderRight: '0.5px solid var(--border)'}}>
            <div style={{display:'flex', gap: 8, marginBottom: 16, paddingBottom: 12, borderBottom: '0.5px solid var(--border)'}}>
              <span style={{fontSize: 12, fontWeight: 500, color: 'var(--purple)', borderBottom:'1.5px solid var(--purple)', paddingBottom: 8}}>Resume → Jobs</span>
              <span style={{fontSize: 12, color: 'var(--ink-500)', paddingBottom: 8}}>Job → Resumes</span>
              <span style={{fontSize: 12, color: 'var(--ink-500)', paddingBottom: 8}}>One-to-one</span>
            </div>
            <div style={{
              border: '1.5px dashed var(--border-strong)',
              borderRadius: 8,
              padding: '20px 16px',
              textAlign: 'center'
            }}>
              <div className="upload-icon" style={{margin:'0 auto 8px'}}>
                <Icon.Upload size={16} />
              </div>
              <div style={{fontSize: 12, fontWeight: 500}}>Drop your resume here</div>
              <div style={{fontSize: 11, color:'var(--ink-500)', marginTop: 2}}>PDF, DOCX, or TXT</div>
            </div>
            <div style={{marginTop: 16, display:'flex', gap: 8}}>
              <div style={{flex:1, height: 30, borderRadius: 8, border:'0.5px solid var(--border)', display:'flex', alignItems:'center', padding:'0 10px', fontSize: 11, color:'var(--ink-500)'}}>bge-large-en-v1.5</div>
              <div style={{width: 50, height: 30, borderRadius: 8, border:'0.5px solid var(--border)', display:'flex', alignItems:'center', justifyContent:'center', fontSize: 11}}>5</div>
              <button className="btn btn-primary" style={{height: 30, fontSize: 11}}>Match</button>
            </div>
          </div>
          <div style={{padding: 16, background: 'var(--bg-soft)'}}>
            <div style={{padding: '4px 4px 12px', display:'flex', alignItems:'center', justifyContent:'space-between'}}>
              <span style={{fontSize: 12, fontWeight: 500}}>Top matches</span>
              <span style={{fontSize: 11, color:'var(--ink-500)'}}>5 results</span>
            </div>
            {MOCK_JOBS.slice(0,3).map(j => (
              <div key={j.id} style={{
                background:'#fff', border:'0.5px solid var(--border)', borderRadius: 12,
                padding: 14, marginBottom: 8
              }}>
                <div style={{display:'flex', justifyContent:'space-between', alignItems:'flex-start', gap: 12}}>
                  <div>
                    <div style={{fontSize: 13, fontWeight: 500}}>{j.title}</div>
                    <div style={{fontSize: 11, color:'var(--ink-500)', marginTop: 2}}>{j.company} · {j.location}</div>
                  </div>
                  <ScoreBadge value={j.score} />
                </div>
                <ScoreBar value={j.score} animate={false} />
                <div className="pills" style={{marginTop: 0}}>
                  {j.matched.slice(0,3).map(s => <Pill key={s}>{s}</Pill>)}
                  {j.missing.slice(0,1).map(s => <Pill key={s} miss>{s}</Pill>)}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function HowItWorks() {
  return (
    <section className="section" id="how" data-screen-label="How it works">
      <h2 className="section-title">How it works</h2>
      <p className="section-sub">Three steps, zero setup.</p>
      <div className="card-grid">
        <div className="feature-card">
          <div className="feature-icon"><Icon.Upload size={18}/></div>
          <h3 className="feature-title">Upload or paste</h3>
          <p className="feature-desc">Drop a resume or job description in PDF, DOCX, or plain text. We extract structure automatically.</p>
        </div>
        <div className="feature-card">
          <div className="feature-icon"><Icon.Brain size={18}/></div>
          <h3 className="feature-title">Semantic matching</h3>
          <p className="feature-desc">Transformer models encode your text into dense vector embeddings tuned for hiring context.</p>
        </div>
        <div className="feature-card">
          <div className="feature-icon"><Icon.Chart size={18}/></div>
          <h3 className="feature-title">Ranked results</h3>
          <p className="feature-desc">Cosine similarity ranks every candidate with a confidence score, matched skills, and gaps.</p>
        </div>
      </div>
    </section>
  );
}

function ModelStrip() {
  return (
    <section className="section" style={{paddingTop: 0}}>
      <div style={{
        border: '0.5px solid var(--border)',
        borderRadius: 12,
        padding: '24px 28px',
        display: 'grid',
        gridTemplateColumns: '1fr 2fr',
        gap: 28,
        alignItems: 'center'
      }}>
        <div>
          <div style={{fontSize: 12, color:'var(--purple-700)', fontWeight: 500, marginBottom: 6}}>Models we ship with</div>
          <div style={{fontSize: 18, fontWeight: 500, letterSpacing:'-0.01em', marginBottom: 6}}>Switch embeddings without re-indexing.</div>
          <div style={{fontSize: 13, color:'var(--ink-500)', lineHeight: 1.55}}>
            Pick from open-source encoders, swap in your own checkpoint, or layer a cross-encoder reranker on top.
          </div>
        </div>
        <div style={{display:'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 8}}>
          {MODELS.map(m => (
            <div key={m.id} style={{
              border:'0.5px solid var(--border)',
              borderRadius: 8,
              padding: '12px 14px',
              display:'flex',
              alignItems:'center',
              justifyContent:'space-between',
              gap: 12
            }}>
              <div style={{minWidth: 0}}>
                <div className="mono" style={{fontSize: 11, fontWeight: 500, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap'}}>{m.name}</div>
                <div style={{fontSize: 11, color:'var(--ink-500)', marginTop: 2}}>{m.dims} dims</div>
              </div>
              {m.recommended && <span className="pill match" style={{fontSize: 10}}><Icon.Check size={10}/> Default</span>}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function CTABanner({ onRoute }) {
  return (
    <section className="cta-banner">
      <div className="cta-inner">
        <p className="cta-text">Ready to streamline your hiring?</p>
        <button className="btn btn-primary btn-lg" onClick={()=>onRoute('match')}>
          Start matching <Icon.Arrow />
        </button>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="footer" data-screen-label="Footer">
      <div className="footer-inner">
        <div className="brand">
          <Logo size={18} />
          <span className="brand-name" style={{fontSize: 13}}>Matchr</span>
          <span style={{fontSize: 11, color:'var(--ink-400)', marginLeft: 8}}>© 2026</span>
        </div>
        <div className="footer-links">
          <a className="footer-link" href="https://github.com/MohamedGamal04">GitHub</a>
          <a className="footer-link" href="https://www.linkedin.com/in/mohamedgamal-zarouk">Contact</a>
        </div>
      </div>
    </footer>
  );
}

function Landing({ onRoute }) {
  return (
    <div data-screen-label="01 Landing">
      <Hero onRoute={onRoute} />
      <HeroPreview />
      <HowItWorks />
      <ModelStrip />
      <CTABanner onRoute={onRoute} />
      <Footer />
    </div>
  );
}

Object.assign(window, { Nav, Landing });
