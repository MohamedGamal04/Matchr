// App root — hash routing + optional cold-start banner

const API_BASE_FALLBACK =
  (typeof API_BASE !== 'undefined' ? API_BASE
   : (typeof window !== 'undefined' && window.MATCHR_API) || 'http://localhost:8000');

function App() {
  // Hash routing
  const parseRoute = () => {
    const h = (window.location.hash || '#/').replace(/^#/, '');
    if (h.startsWith('/match')) return 'match';
    if (h.startsWith('/add')) return 'add';
    return 'landing';
  };
  const [route, setRoute] = React.useState(parseRoute);
  React.useEffect(() => {
    const fn = () => setRoute(parseRoute());
    window.addEventListener('hashchange', fn);
    return () => window.removeEventListener('hashchange', fn);
  }, []);
  const goto = (r) => {
    window.location.hash = r === 'landing' ? '/' : `/${r}`;
    setRoute(r);
    window.scrollTo({ top: 0, behavior: 'instant' });
  };

  // Cold-start detection: ping /api/health on first paint. If it doesn't
  // respond within ~3s we assume the HF Space is waking up and show a banner.
  const [warming, setWarming] = React.useState(false);
  React.useEffect(() => {
    let cancelled = false;
    const warmTimer = setTimeout(() => { if (!cancelled) setWarming(true); }, 3000);
    fetch(`${API_BASE_FALLBACK}/api/health`)
      .catch(() => {})
      .finally(() => {
        if (cancelled) return;
        clearTimeout(warmTimer);
        setWarming(false);
      });
    return () => { cancelled = true; clearTimeout(warmTimer); };
  }, []);

  return (
    <div className="app">
      <Nav route={route} onRoute={goto} />
      {warming && <ColdStartBanner />}
      {route === 'landing' && <Landing onRoute={goto} />}
      {route === 'match' && <MatchPage />}
      {route === 'add' && <AddDataPage />}
    </div>
  );
}

function ColdStartBanner() {
  return (
    <div style={{
      padding: '10px 16px',
      background: 'var(--purple-50)',
      borderBottom: '0.5px solid var(--border)',
      fontSize: 12,
      color: 'var(--purple-700)',
      textAlign: 'center',
    }}>
      ⏳ Warming up the embedding models on the backend — first request after sleep
      takes about a minute. Hang tight…
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App/>);
