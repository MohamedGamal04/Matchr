// Shared primitives: icons, Logo, Nav, ScoreBar, ScoreBadge, Pill

const Icon = {
  Sparkle: (p) => (
    <svg width={p.size||14} height={p.size||14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" {...p}>
      <path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M5.6 18.4l2.8-2.8M15.6 8.4l2.8-2.8"/>
    </svg>
  ),
  Search: (p) => (
    <svg width={p.size||14} height={p.size||14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" {...p}>
      <circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>
    </svg>
  ),
  Doc: (p) => (
    <svg width={p.size||14} height={p.size||14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" {...p}>
      <path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/>
      <path d="M14 3v6h6"/><path d="M8 13h8M8 17h5"/>
    </svg>
  ),
  Briefcase: (p) => (
    <svg width={p.size||14} height={p.size||14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" {...p}>
      <rect x="3" y="7" width="18" height="13" rx="2"/>
      <path d="M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2"/>
      <path d="M3 13h18"/>
    </svg>
  ),
  Swap: (p) => (
    <svg width={p.size||14} height={p.size||14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" {...p}>
      <path d="M7 10 4 7l3-3"/><path d="M4 7h12a4 4 0 0 1 4 4"/>
      <path d="m17 14 3 3-3 3"/><path d="M20 17H8a4 4 0 0 1-4-4"/>
    </svg>
  ),
  Upload: (p) => (
    <svg width={p.size||16} height={p.size||16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" {...p}>
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
      <path d="M17 8l-5-5-5 5"/><path d="M12 3v12"/>
    </svg>
  ),
  Brain: (p) => (
    <svg width={p.size||16} height={p.size||16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" {...p}>
      <path d="M9 4a3 3 0 0 0-3 3v0a3 3 0 0 0-3 3v0a3 3 0 0 0 1.5 2.6A3 3 0 0 0 6 18a3 3 0 0 0 3 3z"/>
      <path d="M15 4a3 3 0 0 1 3 3v0a3 3 0 0 1 3 3v0a3 3 0 0 1-1.5 2.6A3 3 0 0 1 18 18a3 3 0 0 1-3 3z"/>
      <path d="M9 4h6"/><path d="M9 21h6"/><path d="M12 4v17"/>
    </svg>
  ),
  Chart: (p) => (
    <svg width={p.size||16} height={p.size||16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" {...p}>
      <path d="M3 3v18h18"/><path d="M7 15l4-4 3 3 5-6"/>
    </svg>
  ),
  X: (p) => (
    <svg width={p.size||14} height={p.size||14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" {...p}>
      <path d="M18 6 6 18M6 6l12 12"/>
    </svg>
  ),
  Play: (p) => (
    <svg width={p.size||12} height={p.size||12} viewBox="0 0 24 24" fill="currentColor" {...p}>
      <path d="M8 5v14l11-7z"/>
    </svg>
  ),
  Arrow: (p) => (
    <svg width={p.size||14} height={p.size||14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" {...p}>
      <path d="M5 12h14M13 5l7 7-7 7"/>
    </svg>
  ),
  ThumbUp: (p) => (
    <svg width={p.size||14} height={p.size||14} viewBox="0 0 24 24" fill={p.filled?'currentColor':'none'} stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" {...p}>
      <path d="M7 11v9H4a1 1 0 0 1-1-1v-7a1 1 0 0 1 1-1h3z"/>
      <path d="M7 11l4-8a2 2 0 0 1 2 2v4h6a2 2 0 0 1 2 2.4l-1.5 7A2 2 0 0 1 17.5 20H7"/>
    </svg>
  ),
  ThumbDown: (p) => (
    <svg width={p.size||14} height={p.size||14} viewBox="0 0 24 24" fill={p.filled?'currentColor':'none'} stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" {...p}>
      <path d="M17 13V4h3a1 1 0 0 1 1 1v7a1 1 0 0 1-1 1h-3z"/>
      <path d="M17 13l-4 8a2 2 0 0 1-2-2v-4H5a2 2 0 0 1-2-2.4l1.5-7A2 2 0 0 1 6.5 4H17"/>
    </svg>
  ),
  MoneyDot: (p) => (
    <svg width={p.size||12} height={p.size||12} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" {...p}>
      <circle cx="12" cy="12" r="9"/><path d="M15 9.5a3 3 0 0 0-3-1.5c-1.7 0-3 1-3 2.3s1.3 1.7 3 2.2 3 .9 3 2.2-1.3 2.3-3 2.3a3 3 0 0 1-3-1.5"/><path d="M12 6v2M12 16v2"/>
    </svg>
  ),
  Star: (p) => (
    <svg width={p.size||12} height={p.size||12} viewBox="0 0 24 24" fill="currentColor" {...p}>
      <path d="m12 2 3 6.5L22 9l-5 4.7 1.3 7L12 17.3 5.7 20.7 7 13.7 2 9l7-.5z"/>
    </svg>
  ),
  Cap: (p) => (
    <svg width={p.size||12} height={p.size||12} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" {...p}>
      <path d="M22 10 12 5 2 10l10 5 10-5z"/><path d="M6 12v5c0 1 3 3 6 3s6-2 6-3v-5"/>
    </svg>
  ),
  Check: (p) => (
    <svg width={p.size||12} height={p.size||12} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...p}>
      <path d="m5 12 5 5L20 7"/>
    </svg>
  ),
};

function Logo({ size = 22 }) {
  return (
    <div className="logo-mark" style={{width:size, height:size}}>
      <svg width={size*0.62} height={size*0.62} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="10" cy="10" r="6"/>
        <path d="m20 20-5-5"/>
        <path d="M8 10h4M10 8v4" strokeWidth="2"/>
      </svg>
    </div>
  );
}

function tierFor(score) {
  if (score >= 0.80) return 'high';
  if (score >= 0.65) return 'mid';
  return 'low';
}
function labelFor(score) {
  if (score >= 0.90) return 'Excellent match';
  if (score >= 0.80) return 'Strong match';
  if (score >= 0.70) return 'Very good match';
  if (score >= 0.65) return 'Good match';
  if (score >= 0.55) return 'Fair match';
  return 'Weak match';
}

function ScoreBar({ value, large, animate = true }) {
  const tier = tierFor(value);
  const [w, setW] = React.useState(animate ? 0 : value * 100);
  React.useEffect(() => {
    if (!animate) { setW(value * 100); return; }
    const id = requestAnimationFrame(() => setW(value * 100));
    return () => cancelAnimationFrame(id);
  }, [value, animate]);
  return (
    <div className={`score-bar-wrap ${large ? 'lg' : ''}`}>
      <div className={`score-bar ${tier}`} style={{ width: `${w}%` }} />
    </div>
  );
}

function ScoreBadge({ value }) {
  const tier = tierFor(value);
  return (
    <span className={`score-badge ${tier}`}>{Math.round(value * 100)}%</span>
  );
}

function Pill({ children, miss }) {
  return <span className={`pill ${miss ? 'miss' : 'match'}`}>{children}</span>;
}

Object.assign(window, { Icon, Logo, tierFor, labelFor, ScoreBar, ScoreBadge, Pill });
