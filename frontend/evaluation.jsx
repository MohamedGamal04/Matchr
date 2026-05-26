// Evaluation dashboard

function MetricCard({ label, value, delta, deltaDir = 'up', suffix }) {
  return (
    <div className="metric-card">
      <div className="metric-label">
        <span>{label}</span>
        <span className="tiny muted">30d</span>
      </div>
      <div className="metric-value">{value}<span style={{fontSize: 14, color:'var(--ink-400)', marginLeft: 2}}>{suffix}</span></div>
      {delta && (
        <div className={`metric-delta ${deltaDir==='down'?'down':''}`}>
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            {deltaDir==='down' ? <path d="M6 9l6 6 6-6"/> : <path d="M6 15l6-6 6 6"/>}
          </svg>
          {delta}
        </div>
      )}
    </div>
  );
}

function TrendChart() {
  const { ndcg, mrr } = TREND_SERIES;
  const W = 720, H = 220, P = { l: 32, r: 16, t: 14, b: 26 };
  const innerW = W - P.l - P.r;
  const innerH = H - P.t - P.b;
  const min = 0.6, max = 0.95;
  const x = (i) => P.l + (i / (ndcg.length - 1)) * innerW;
  const y = (v) => P.t + (1 - (v - min) / (max - min)) * innerH;

  const toPath = (arr) => arr.map((v,i) => `${i===0?'M':'L'} ${x(i).toFixed(1)} ${y(v).toFixed(1)}`).join(' ');
  const toArea = (arr) => `${toPath(arr)} L ${x(arr.length-1)} ${P.t+innerH} L ${x(0)} ${P.t+innerH} Z`;

  const yTicks = [0.6, 0.7, 0.8, 0.9];

  return (
    <div className="chart-card">
      <div className="chart-head">
        <div>
          <div className="chart-title">Ranking quality, last 30 days</div>
          <div className="tiny muted mt-1">Updated 2 min ago · Production traffic</div>
        </div>
        <div className="chart-legend">
          <span className="legend-item"><span className="legend-swatch" style={{background:'var(--purple)'}}/> NDCG@5</span>
          <span className="legend-item"><span className="legend-swatch" style={{background:'var(--green-500)'}}/> MRR</span>
        </div>
      </div>
      <div style={{width:'100%', overflow:'hidden'}}>
        <svg width="100%" viewBox={`0 0 ${W} ${H}`} style={{display:'block'}}>
          <defs>
            <linearGradient id="purpleGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#6C5CE7" stopOpacity="0.15"/>
              <stop offset="100%" stopColor="#6C5CE7" stopOpacity="0"/>
            </linearGradient>
          </defs>
          {/* y grid */}
          {yTicks.map(t => (
            <g key={t}>
              <line x1={P.l} x2={W - P.r} y1={y(t)} y2={y(t)} stroke="rgba(17,17,20,0.06)" strokeWidth="0.5"/>
              <text x={P.l - 8} y={y(t)} textAnchor="end" dominantBaseline="middle" fontSize="10" fill="#9aa0a6">{t.toFixed(1)}</text>
            </g>
          ))}
          {/* x labels */}
          {[0, 7, 14, 21, 29].map(i => (
            <text key={i} x={x(i)} y={H - 8} textAnchor="middle" fontSize="10" fill="#9aa0a6">
              {i === 29 ? 'today' : `d-${29-i}`}
            </text>
          ))}
          {/* area under NDCG */}
          <path d={toArea(ndcg)} fill="url(#purpleGrad)"/>
          {/* lines */}
          <path d={toPath(ndcg)} fill="none" stroke="#6C5CE7" strokeWidth="1.5" strokeLinejoin="round"/>
          <path d={toPath(mrr)} fill="none" stroke="#22C55E" strokeWidth="1.5" strokeLinejoin="round"/>
          {/* end-point dots */}
          <circle cx={x(ndcg.length-1)} cy={y(ndcg[ndcg.length-1])} r="3" fill="#6C5CE7"/>
          <circle cx={x(mrr.length-1)} cy={y(mrr[mrr.length-1])} r="3" fill="#22C55E"/>
        </svg>
      </div>
    </div>
  );
}

function Donut() {
  const total = FEEDBACK.up + FEEDBACK.down + FEEDBACK.none;
  const pUp = FEEDBACK.up / total;
  const pDown = FEEDBACK.down / total;
  const pNone = FEEDBACK.none / total;

  const R = 52, S = 14;
  const C = 2 * Math.PI * R;
  const offUp = 0;
  const offDown = C * pUp;
  const offNone = C * (pUp + pDown);

  return (
    <div className="chart-card">
      <div className="chart-head">
        <div>
          <div className="chart-title">User feedback</div>
          <div className="tiny muted mt-1">{total.toLocaleString()} rated results</div>
        </div>
      </div>
      <div className="donut-wrap">
        <svg width="128" height="128" viewBox="0 0 128 128">
          <circle cx="64" cy="64" r={R} fill="none" stroke="var(--bg-softer)" strokeWidth={S}/>
          <circle cx="64" cy="64" r={R} fill="none" stroke="var(--purple)" strokeWidth={S}
                  strokeDasharray={`${C * pUp} ${C}`} strokeDashoffset={-offUp} transform="rotate(-90 64 64)" strokeLinecap="butt"/>
          <circle cx="64" cy="64" r={R} fill="none" stroke="var(--amber-500)" strokeWidth={S}
                  strokeDasharray={`${C * pDown} ${C}`} strokeDashoffset={-offDown} transform="rotate(-90 64 64)"/>
          <circle cx="64" cy="64" r={R} fill="none" stroke="#E5E7EB" strokeWidth={S}
                  strokeDasharray={`${C * pNone} ${C}`} strokeDashoffset={-offNone} transform="rotate(-90 64 64)"/>
          <text x="64" y="60" textAnchor="middle" fontSize="20" fontWeight="500" fill="var(--ink-900)">{Math.round(pUp*100)}%</text>
          <text x="64" y="76" textAnchor="middle" fontSize="10" fill="var(--ink-500)">positive</text>
        </svg>
        <div className="donut-legend">
          <div className="donut-row">
            <span className="donut-row-label">
              <span className="legend-swatch" style={{background:'var(--purple)', borderRadius: 999}}/>
              Thumbs up
            </span>
            <span className="mono tiny">{FEEDBACK.up}</span>
          </div>
          <div className="donut-row">
            <span className="donut-row-label">
              <span className="legend-swatch" style={{background:'var(--amber-500)', borderRadius: 999}}/>
              Thumbs down
            </span>
            <span className="mono tiny">{FEEDBACK.down}</span>
          </div>
          <div className="donut-row">
            <span className="donut-row-label">
              <span className="legend-swatch" style={{background:'#E5E7EB', borderRadius: 999}}/>
              No feedback
            </span>
            <span className="mono tiny">{FEEDBACK.none}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function ModelTable() {
  return (
    <div className="chart-card" style={{padding: 0, overflow:'hidden'}}>
      <div style={{padding: '18px 20px', borderBottom: '0.5px solid var(--border)', display:'flex', justifyContent:'space-between', alignItems:'flex-end'}}>
        <div>
          <div className="chart-title">Model comparison</div>
          <div className="tiny muted mt-1">A/B traffic across {MODEL_COMPARE.reduce((s,m)=>s+m.queries,0).toLocaleString()} queries</div>
        </div>
        <button className="btn btn-ghost" style={{height: 28, fontSize: 12}}>Export CSV</button>
      </div>
      <table className="table">
        <thead>
          <tr>
            <th>Model</th>
            <th>Reranked</th>
            <th style={{textAlign:'right'}}>Queries</th>
            <th style={{textAlign:'right'}}>NDCG@5</th>
            <th style={{textAlign:'right'}}>MRR</th>
            <th style={{textAlign:'right'}}>P@5</th>
            <th style={{textAlign:'right'}}>Latency</th>
          </tr>
        </thead>
        <tbody>
          {MODEL_COMPARE.map(m => (
            <tr key={m.name}>
              <td><span className="mono">{m.name}</span></td>
              <td>
                {m.reranked
                  ? <span className="pill match" style={{fontSize: 10}}><Icon.Check size={10}/> Yes</span>
                  : <span className="pill miss" style={{fontSize: 10}}>No</span>}
              </td>
              <td style={{textAlign:'right'}} className="mono">{m.queries.toLocaleString()}</td>
              <td style={{textAlign:'right'}} className="mono">{m.ndcg.toFixed(2)}</td>
              <td style={{textAlign:'right'}} className="mono">{m.mrr.toFixed(2)}</td>
              <td style={{textAlign:'right'}} className="mono">{m.p5.toFixed(2)}</td>
              <td style={{textAlign:'right'}} className="mono">{m.latency}ms</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function EvalPage() {
  return (
    <div className="eval-shell" data-screen-label="03 Evaluation">
      <div className="match-head">
        <div>
          <h1 className="match-h">Evaluation</h1>
          <p className="match-sub">How well Matchr is ranking, in production.</p>
        </div>
        <div style={{display:'flex', gap: 8, alignItems:'center'}}>
          <div className="select-wrap" style={{width: 140}}>
            <select className="select" defaultValue="30d">
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="90d">Last 90 days</option>
            </select>
          </div>
          <button className="btn btn-ghost">Run eval</button>
        </div>
      </div>

      <div className="metric-grid">
        <MetricCard label="NDCG@5" value="0.89" delta="+0.03 vs prev"/>
        <MetricCard label="MRR" value="0.86" delta="+0.04 vs prev"/>
        <MetricCard label="Precision@5" value="0.82" delta="+0.01 vs prev"/>
        <MetricCard label="Avg latency" value="340" suffix="ms" delta="−18ms vs prev"/>
      </div>

      <div className="dash-grid">
        <TrendChart />
        <Donut />
      </div>

      <ModelTable />
    </div>
  );
}

Object.assign(window, { EvalPage });
