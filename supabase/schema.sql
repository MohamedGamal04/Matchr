-- ============================================================
-- Matchr Database Schema
-- Run this in: Supabase Dashboard → SQL Editor → New Query
-- ============================================================

-- Enable pgvector extension (required for vector columns + HNSW index)
create extension if not exists vector;

-- ── Resumes table ─────────────────────────────────────────────────────────────
create table if not exists resumes (
  id          uuid primary key default gen_random_uuid(),
  source      text,           -- "opensporks/resumes" | "sid1877/Resume-dataset-2024"
  source_id   text unique,    -- original row ID — prevents duplicate inserts on re-run
  category    text,           -- job category label e.g. "Data Science", "Java Developer"
  preview     text,           -- sanitised 250-char snippet shown in UI (PII stripped)
  full_text   text,           -- full resume text used for embedding only — NEVER expose via API
  embedding   vector(1024),   -- BAAI/bge-large-en-v1.5 produces 1024-dim vectors
  created_at  timestamptz default now()
);

-- ── Jobs table ────────────────────────────────────────────────────────────────
create table if not exists jobs (
  id           uuid primary key default gen_random_uuid(),
  source       text,
  source_id    text unique,
  title        text,
  company      text,
  salary       text,
  experience   text,
  work_type    text,          -- "Remote" | "Hybrid" | "On-site"
  skills       text[],        -- array of skill keyword strings
  full_text    text,          -- full JD text used for embedding + reranking
  job_url      text,          -- direct link to the original posting (JobSpy)
  company_url  text,          -- company website / profile URL (JobSpy)
  embedding    vector(1024),
  created_at   timestamptz default now()
);

-- ── Evaluations table ─────────────────────────────────────────────────────────
-- Query log for every match request. IR-relevance metrics were dropped:
-- we collect raw feedback signals in `user_feedback` for later analysis,
-- but don't aggregate them into NDCG/MRR/P@5 columns or a summary view.
create table if not exists evaluations (
  id               uuid primary key default gen_random_uuid(),
  query_text       text not null,
  query_type       text check (query_type in ('resume_to_jobs','job_to_resumes','one_to_one')),
  model_name       text not null,
  reranked         boolean default false,
  result_ids       uuid[],            -- ordered list of result UUIDs shown to user
  similarity_scores float[],
  rerank_scores    float[],
  user_feedback    jsonb default '{}', -- {result_id: "up"|"down"|"clicked"}
  latency_ms       int,
  created_at       timestamptz default now()
);

-- ── HNSW indexes for fast approximate nearest-neighbour search ────────────────
-- m=16, ef_construction=64 is a good balance of speed vs. recall for this scale.
create index if not exists resumes_embedding_idx
  on resumes using hnsw (embedding vector_cosine_ops)
  with (m = 16, ef_construction = 64);

create index if not exists jobs_embedding_idx
  on jobs using hnsw (embedding vector_cosine_ops)
  with (m = 16, ef_construction = 64);

-- ── Supporting indexes ────────────────────────────────────────────────────────
create index if not exists resumes_category_idx on resumes (category);
create index if not exists jobs_title_idx       on jobs    (title);


-- ── Similarity search RPC functions ──────────────────────────────────────────

-- Job → Resumes: given a job embedding, find the most similar resumes
create or replace function match_resumes(
  query_embedding  vector(1024),
  match_count      int     default 50,
  filter_category  text    default null
)
returns table (
  id         uuid,
  category   text,
  preview    text,        -- ONLY preview is returned, never full_text
  similarity float
)
language sql stable as $$
  select
    id,
    category,
    preview,
    1 - (embedding <=> query_embedding) as similarity
  from resumes
  where
    filter_category is null or category = filter_category
  order by embedding <=> query_embedding
  limit match_count;
$$;

-- Resume → Jobs: given a resume embedding, find the most similar jobs
create or replace function match_jobs(
  query_embedding vector(1024),
  match_count     int default 50
)
returns table (
  id         uuid,
  title      text,
  company    text,
  salary     text,
  experience text,
  work_type  text,
  skills     text[],
  similarity float
)
language sql stable as $$
  select
    id,
    title,
    company,
    salary,
    experience,
    work_type,
    skills,
    1 - (embedding <=> query_embedding) as similarity
  from jobs
  order by embedding <=> query_embedding
  limit match_count;
$$;


-- ── Analytics views ───────────────────────────────────────────────────────────

create or replace view resume_category_counts as
  select category, count(*) as total
  from resumes
  group by category
  order by total desc;


-- ── Section-aware retrieval ───────────────────────────────────────────────────

create table if not exists resume_sections (
  id           uuid primary key default gen_random_uuid(),
  resume_id    uuid not null references resumes(id) on delete cascade,
  section_type text not null check (section_type in ('experience','skills','education','summary','other')),
  content      text not null,
  embedding    vector(1024),
  created_at   timestamptz default now(),
  unique (resume_id, section_type)
);

create index if not exists resume_sections_resume_id_idx
  on resume_sections (resume_id);

create index if not exists resume_sections_embedding_idx
  on resume_sections using hnsw (embedding vector_cosine_ops)
  with (m = 16, ef_construction = 64);

create or replace function match_resumes_sectioned(
  query_embedding vector(1024),
  match_count     int default 50
)
returns table (
  resume_id    uuid,
  category     text,
  preview      text,
  similarity   float,
  best_section text
)
language sql stable as $$
  select
    r.id as resume_id,
    r.category,
    r.preview,
    max(1 - (s.embedding <=> query_embedding)) as similarity,
    (array_agg(s.section_type order by (s.embedding <=> query_embedding) asc))[1] as best_section
  from resume_sections s
  join resumes r on r.id = s.resume_id
  group by r.id, r.category, r.preview
  order by similarity desc
  limit match_count;
$$;
