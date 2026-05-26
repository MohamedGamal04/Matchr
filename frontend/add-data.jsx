// Add Data page — submit resumes / jobs into the live Supabase database.

const ADD_API_BASE = (typeof API_BASE !== 'undefined' ? API_BASE : 'http://localhost:8000');

async function apiIngest(kind, body) {
  const res = await fetch(`${ADD_API_BASE}/api/ingest/${kind}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const json = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = json.detail;
    const msg = (typeof formatDetail === 'function')
      ? formatDetail(detail, res.status)
      : (typeof detail === 'string' ? detail : `HTTP ${res.status}`);
    throw new Error(msg);
  }
  return json;
}

const RESUME_CATEGORY_SUGGESTIONS = [
  'Accountant', 'Advocate', 'Agriculture', 'Apparel', 'Arts', 'Automobile',
  'Aviation', 'Banking', 'BPO', 'Business Development', 'Chef', 'Construction',
  'Consultant', 'Data Science', 'Database Administrator', 'Designer',
  'Digital Media', 'Engineering', 'Finance', 'Fitness', 'HR', 'Healthcare',
  'Information Technology', 'Java Developer', 'Network Administrator',
  'Project manager', 'Public Relations', 'Python Developer', 'Sales',
  'Security Analyst', 'Software Developer', 'Systems Administrator',
  'Teacher', 'Web Developer'
];

function AddResumeForm() {
  const [category, setCategory] = React.useState('');
  const [text, setText] = React.useState('');
  const [busy, setBusy] = React.useState(false);
  const [status, setStatus] = React.useState(null); // {ok, msg}

  const submit = async () => {
    setBusy(true);
    setStatus(null);
    try {
      const data = await apiIngest('resume', {
        category: category.trim(),
        full_text: text,
      });
      setStatus({ ok: true, msg: data.message || 'Resume added.' });
      setText('');
    } catch (e) {
      setStatus({ ok: false, msg: e.message });
    } finally {
      setBusy(false);
    }
  };

  const disabled = busy || category.trim().length < 2 || text.trim().length < 50;

  return (
    <div className="panel-pad" style={{display:'flex', flexDirection:'column', gap: 14}}>
      <div>
        <label className="label">Category</label>
        <input
          className="select"
          list="resume-category-list"
          placeholder="e.g. Python Developer"
          value={category}
          onChange={(e)=>setCategory(e.target.value)}
        />
        <datalist id="resume-category-list">
          {RESUME_CATEGORY_SUGGESTIONS.map(c => <option key={c} value={c} />)}
        </datalist>
      </div>
      <div>
        <label className="label">Resume text</label>
        <textarea
          className="textarea"
          style={{minHeight: 260}}
          placeholder="Paste the full resume text — skills, experience, education…"
          value={text}
          onChange={(e)=>setText(e.target.value)}
        />
        <div className="tiny muted" style={{marginTop: 4}}>
          {text.trim().length} characters · min 50 required
        </div>
      </div>
      <div style={{display:'flex', justifyContent:'flex-end'}}>
        <button className="btn btn-primary" disabled={disabled} onClick={submit}>
          {busy ? 'Adding…' : 'Add resume to database'}
        </button>
      </div>
      {status && <StatusBanner ok={status.ok} msg={status.msg} />}
    </div>
  );
}

function AddJobForm() {
  const [title, setTitle] = React.useState('');
  const [company, setCompany] = React.useState('');
  const [salary, setSalary] = React.useState('');
  const [experience, setExperience] = React.useState('');
  const [workType, setWorkType] = React.useState('');
  const [skillsInput, setSkillsInput] = React.useState('');
  const [text, setText] = React.useState('');
  const [busy, setBusy] = React.useState(false);
  const [status, setStatus] = React.useState(null);

  const submit = async () => {
    setBusy(true);
    setStatus(null);
    try {
      const skills = skillsInput
        .split(/[,\n;]+/)
        .map(s => s.trim())
        .filter(s => s.length > 0);
      const data = await apiIngest('job', {
        title:      title.trim(),
        company:    company.trim() || null,
        salary:     salary.trim() || null,
        experience: experience.trim() || null,
        work_type:  workType.trim() || null,
        skills,
        full_text:  text,
      });
      setStatus({ ok: true, msg: data.message || 'Job added.' });
      setText('');
    } catch (e) {
      setStatus({ ok: false, msg: e.message });
    } finally {
      setBusy(false);
    }
  };

  const disabled = busy || title.trim().length < 2 || text.trim().length < 50;

  return (
    <div className="panel-pad" style={{display:'flex', flexDirection:'column', gap: 14}}>
      <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap: 12}}>
        <div>
          <label className="label">Job title *</label>
          <input className="select" placeholder="e.g. Senior Python Developer"
            value={title} onChange={(e)=>setTitle(e.target.value)} />
        </div>
        <div>
          <label className="label">Company</label>
          <input className="select" placeholder="Optional"
            value={company} onChange={(e)=>setCompany(e.target.value)} />
        </div>
        <div>
          <label className="label">Salary</label>
          <input className="select" placeholder="$120k–150k"
            value={salary} onChange={(e)=>setSalary(e.target.value)} />
        </div>
        <div>
          <label className="label">Experience</label>
          <input className="select" placeholder="3+ years"
            value={experience} onChange={(e)=>setExperience(e.target.value)} />
        </div>
        <div>
          <label className="label">Work type</label>
          <input className="select" list="work-type-list" placeholder="Full-Time / Remote / Hybrid"
            value={workType} onChange={(e)=>setWorkType(e.target.value)} />
          <datalist id="work-type-list">
            <option value="Full-Time" />
            <option value="Part-Time" />
            <option value="Remote" />
            <option value="Hybrid" />
            <option value="On-site" />
            <option value="Contract" />
            <option value="Intern" />
          </datalist>
        </div>
        <div>
          <label className="label">Skills (comma-separated)</label>
          <input className="select" placeholder="Python, FastAPI, PostgreSQL"
            value={skillsInput} onChange={(e)=>setSkillsInput(e.target.value)} />
        </div>
      </div>
      <div>
        <label className="label">Job description *</label>
        <textarea
          className="textarea"
          style={{minHeight: 220}}
          placeholder="Paste the full job description — responsibilities, requirements…"
          value={text}
          onChange={(e)=>setText(e.target.value)}
        />
        <div className="tiny muted" style={{marginTop: 4}}>
          {text.trim().length} characters · min 50 required
        </div>
      </div>
      <div style={{display:'flex', justifyContent:'flex-end'}}>
        <button className="btn btn-primary" disabled={disabled} onClick={submit}>
          {busy ? 'Adding…' : 'Add job to database'}
        </button>
      </div>
      {status && <StatusBanner ok={status.ok} msg={status.msg} />}
    </div>
  );
}

function StatusBanner({ ok, msg }) {
  const bg = ok ? '#ECFDF5' : '#FEF2F2';
  const color = ok ? '#047857' : '#EF4444';
  return (
    <div style={{padding:'12px 16px', background: bg, borderRadius: 8, fontSize: 12, color}}>
      {ok ? '✓ ' : '⚠ '}{msg}
    </div>
  );
}

function AddDataPage() {
  const [tab, setTab] = React.useState('resume');
  return (
    <div className="match-shell" data-screen-label="Add data">
      <div className="match-head">
        <div>
          <h1 className="match-h">Add to database</h1>
          <p className="match-sub">
            Contribute a new resume or job posting. Text is embedded with{' '}
            <span className="mono">BAAI/bge-large-en-v1.5</span> and inserted into Supabase.
          </p>
        </div>
      </div>
      <section className="panel">
        <div className="tabs" role="tablist">
          <button className={`tab ${tab==='resume'?'active':''}`} onClick={()=>setTab('resume')} role="tab">
            <Icon.Doc size={13}/> Add resume
          </button>
          <button className={`tab ${tab==='job'?'active':''}`} onClick={()=>setTab('job')} role="tab">
            <Icon.Briefcase size={13}/> Add job
          </button>
        </div>
        {tab === 'resume' ? <AddResumeForm /> : <AddJobForm />}
      </section>
    </div>
  );
}

Object.assign(window, { AddDataPage });
