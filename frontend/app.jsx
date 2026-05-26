// App root — routing + Tweaks panel

const TWEAK_DEFAULTS = {
  "accent": "#6C5CE7",
  "density": "comfortable",
  "borderStyle": "hairline",
  "showFeedback": true
};

const ACCENT_OPTIONS = [
  '#6C5CE7', // brand purple
  '#7C3AED', // saturated violet
  '#2A6FDB', // electric blue
  '#1F8A5B'  // forest green
];

function App() {
  // Hash routing
  const parseRoute = () => {
    const h = (window.location.hash || '#/').replace(/^#/, '');
    if (h.startsWith('/match')) return 'match';
    if (h.startsWith('/eval')) return 'eval';
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

  const [tweaks, setTweak] = useTweaks(TWEAK_DEFAULTS);

  // Apply tweaks via CSS vars
  React.useEffect(() => {
    const root = document.documentElement;
    const accent = tweaks.accent;
    root.style.setProperty('--purple', accent);
    root.style.setProperty('--purple-hover', shade(accent, -0.08));
    root.style.setProperty('--purple-pressed', shade(accent, -0.16));
    root.style.setProperty('--purple-50', tint(accent, 0.94));
    root.style.setProperty('--purple-100', tint(accent, 0.88));
    root.style.setProperty('--purple-200', tint(accent, 0.78));
    root.style.setProperty('--purple-700', shade(accent, -0.32));

    if (tweaks.density === 'compact') {
      root.style.setProperty('--r-card', '10px');
    } else {
      root.style.setProperty('--r-card', '12px');
    }
    root.style.setProperty('--border', tweaks.borderStyle === 'soft' ? 'rgba(17,17,20,0.12)' : 'rgba(17,17,20,0.08)');
  }, [tweaks.accent, tweaks.density, tweaks.borderStyle]);

  return (
    <div className="app">
      <Nav route={route} onRoute={goto} />
      {route === 'landing' && <Landing onRoute={goto} />}
      {route === 'match' && <MatchPage />}
      {route === 'eval' && <EvalPage />}

      <TweaksPanel title="Tweaks">
        <TweakSection label="Brand">
          <TweakColor
            label="Accent"
            value={tweaks.accent}
            onChange={(v) => setTweak('accent', v)}
            options={ACCENT_OPTIONS}
          />
        </TweakSection>
        <TweakSection label="Layout">
          <TweakRadio
            label="Density"
            value={tweaks.density}
            onChange={(v) => setTweak('density', v)}
            options={[{value:'comfortable', label:'Comfortable'}, {value:'compact', label:'Compact'}]}
          />
          <TweakRadio
            label="Border weight"
            value={tweaks.borderStyle}
            onChange={(v) => setTweak('borderStyle', v)}
            options={[{value:'hairline', label:'Hairline'}, {value:'soft', label:'Soft'}]}
          />
        </TweakSection>
        <TweakSection label="Result cards">
          <TweakToggle
            label="Show feedback buttons"
            value={tweaks.showFeedback}
            onChange={(v) => setTweak('showFeedback', v)}
          />
        </TweakSection>
      </TweaksPanel>

      {!tweaks.showFeedback && <style>{`.feedback { display: none !important; }`}</style>}
    </div>
  );
}

// Color helpers — hex shading/tinting
function hexToRgb(hex) {
  const h = hex.replace('#','');
  const v = h.length === 3 ? h.split('').map(c=>c+c).join('') : h;
  return [parseInt(v.slice(0,2),16), parseInt(v.slice(2,4),16), parseInt(v.slice(4,6),16)];
}
function rgbToHex([r,g,b]) {
  return '#' + [r,g,b].map(x => Math.max(0, Math.min(255, Math.round(x))).toString(16).padStart(2,'0')).join('');
}
function shade(hex, amount) {
  const [r,g,b] = hexToRgb(hex);
  const f = 1 + amount;
  return rgbToHex([r*f, g*f, b*f]);
}
function tint(hex, t) {
  const [r,g,b] = hexToRgb(hex);
  return rgbToHex([r + (255-r)*t, g + (255-g)*t, b + (255-b)*t]);
}

ReactDOM.createRoot(document.getElementById('root')).render(<App/>);
