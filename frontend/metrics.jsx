// Metrics dashboard page — queries GET /api/eval/metrics

const _METRICS_API_BASE = (typeof window !== 'undefined' && window.MATCHR_API) || 'http://localhost:8000';

function MetricsPage() {
  const [data, setData] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);

  React.useEffect(() => {
    fetch(`${_METRICS_API_BASE}/api/eval/metrics`)
      .then(r => r.ok ? r.json() : r.json().then(e => Promise.reject(new Error(e.detail || `HTTP ${r.status}`))))
      .then(d => { setData(d.metrics || []); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  }, []);

  if (loading) {
    return (<div style={{padding: 60, textAlign: 'center', color: 'var(--ink-500)', fontSize: 14}}>Loading metrics…</div>);
  }
  if (error) {
    return (<div style={{padding: 60, textAlign: 'center', color: '#EF4444', fontSize: 14}}>Failed to load metrics: {error}</div>);
  }
  if (!data || data.length === 0) {
    return (<div style={{padding: 60, textAlign: 'center', color: 'var(--ink-500)', fontSize: 14}}>No metrics yet — run some match queries first.</div>);
  }

  const totals = data.reduce((acc, row) => ({
    queries:    acc.queries    + (Number(row.total_queries)  || 0),
    latencySum: acc.latencySum + (Number(row.avg_latency_ms) || 0) * (Number(row.total_queries) || 0),
    up:         acc.up         + (Number(row.thumbs_up)      || 0),
    down:       acc.down       + (Number(row.thumbs_down)    || 0),
    clicks:     acc.clicks     + (Number(row.clicks)         || 0),
  }), {queries: 0, latencySum: 0, up: 0, down: 0, clicks: 0});

  const avgLatency = totals.queries > 0 ? Math.round(totals.latencySum / totals.queries) : 0;
  const updownTotal = totals.up + totals.down;
  const upRatio = updownTotal > 0 ? `${(totals.up / updownTotal * 100).toFixed(1)}%` : '—';

  const summaryCards = [
    {label: 'Total Queries',   value: totals.queries.toLocaleString()},
    {label: 'Avg Latency',     value: `${avgLatency}ms`},
    {label: 'Thumbs Up',       value: totals.up.toLocaleString()},
    {label: 'Up / Down Ratio', value: upRatio},
    {label: 'Clicks',          value: totals.clicks.toLocaleString()},
  ];

  return (
    <div style={{maxWidth: 960, margin: '0 auto', padding: '40px 20px'}}>
      <h1 style={{fontSize: 22, fontWeight: 700, marginBottom: 6, color: 'var(--ink-900)'}}>Metrics</h1>
      <p style={{fontSize: 13, color: 'var(--ink-500)', marginBottom: 32}}>Aggregated query activity from the evaluations log.</p>

      <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 12, marginBottom: 36}}>
        {summaryCards.map(({label, value}) => (
          <div key={label} style={{padding: '18px 20px', borderRadius: 12, background: 'var(--bg-soft)', border: '0.5px solid var(--border)'}}>
            <div style={{fontSize: 10, fontWeight: 500, color: 'var(--ink-500)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 8}}>{label}</div>
            <div style={{fontSize: 26, fontWeight: 700, color: 'var(--ink-900)'}}>{value}</div>
          </div>
        ))}
      </div>

      <div style={{overflowX: 'auto'}}>
        <table style={{width: '100%', borderCollapse: 'collapse', fontSize: 13}}>
          <thead>
            <tr style={{borderBottom: '1px solid var(--border)'}}>
              {['Day', 'Query Type', 'Reranked', 'Queries', 'Avg Latency', '👍', '👎', 'Clicks'].map(h => (
                <th key={h} style={{textAlign: 'left', padding: '8px 12px', fontWeight: 500, color: 'var(--ink-500)', fontSize: 11, whiteSpace: 'nowrap'}}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, i) => (
              <tr key={i} style={{borderBottom: '0.5px solid var(--border)'}}>
                <td style={{padding: '8px 12px', color: 'var(--ink-700)', whiteSpace: 'nowrap'}}>{row.day ? new Date(row.day).toLocaleDateString() : '—'}</td>
                <td style={{padding: '8px 12px', color: 'var(--ink-700)'}}>{(row.query_type || '—').replace(/_/g, ' ')}</td>
                <td style={{padding: '8px 12px', color: 'var(--ink-500)', textAlign: 'center'}}>{row.reranked ? '✓' : '—'}</td>
                <td style={{padding: '8px 12px', fontVariantNumeric: 'tabular-nums'}}>{row.total_queries}</td>
                <td style={{padding: '8px 12px', color: 'var(--ink-500)', whiteSpace: 'nowrap'}}>{row.avg_latency_ms ? `${Math.round(Number(row.avg_latency_ms))}ms` : '—'}</td>
                <td style={{padding: '8px 12px', color: '#059669'}}>{row.thumbs_up || 0}</td>
                <td style={{padding: '8px 12px', color: '#EF4444'}}>{row.thumbs_down || 0}</td>
                <td style={{padding: '8px 12px', color: 'var(--ink-500)'}}>{row.clicks || 0}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

Object.assign(window, { MetricsPage });
