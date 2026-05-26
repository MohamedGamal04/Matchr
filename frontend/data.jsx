// Mock data for Matchr prototype
const SAMPLE_RESUME = `Maya Chen — Senior Machine Learning Engineer

Experience
• Staff ML Engineer at Foundry AI (2022–present)
  - Led retrieval-augmented generation systems serving 4M queries/day
  - Fine-tuned BGE and E5 embedding models for legal document search
  - Built FAISS + ScaNN hybrid index with 12ms p99 latency
• Senior ML Engineer at Lattice Labs (2019–2022)
  - Shipped transformer-based ranking models in production
  - Reduced inference cost 38% via distillation and ONNX quantization

Skills: PyTorch, Transformers, FAISS, NLP, Python, MLOps, Kubernetes,
sentence-transformers, embeddings, semantic search, reranking, BERT,
GPU optimization, distributed training, HuggingFace, vector databases.

Education
• MS Computer Science, Stanford (NLP focus)
• BS CS, UIUC`;

const SAMPLE_JD = `Senior ML Engineer — Search & Discovery

We're hiring a senior ML engineer to own our semantic search stack.
You'll fine-tune embedding models, design reranking pipelines, and
ship dense retrieval into production at scale.

Required:
• 5+ years ML engineering experience
• Deep PyTorch + Transformers expertise
• Production experience with FAISS or pgvector
• Strong grasp of NLP, sentence embeddings, BERT-family models
• Experience with HuggingFace ecosystem

Nice to have:
• Reranking, cross-encoders, hard negative mining
• MLOps tooling (Kubernetes, distributed training)
• Published research or open-source contributions`;

const MOCK_JOBS = [
  {
    id: 'j1',
    title: 'Senior ML Engineer, Search',
    company: 'Foundry AI',
    location: 'Remote · US',
    type: 'Full-time',
    score: 0.914,
    salary: '$210k–260k',
    experience: '5+ yrs',
    edu: 'MS / PhD preferred',
    matched: ['PyTorch', 'Transformers', 'NLP', 'FAISS', 'Embeddings', 'BERT'],
    missing: ['Cross-encoders', 'ColBERT']
  },
  {
    id: 'j2',
    title: 'Staff Applied Scientist',
    company: 'Nimbus Labs',
    location: 'San Francisco, CA',
    type: 'Hybrid',
    score: 0.872,
    salary: '$240k–300k',
    experience: '7+ yrs',
    edu: 'PhD preferred',
    matched: ['PyTorch', 'Embeddings', 'Semantic search', 'Reranking', 'HuggingFace'],
    missing: ['LLM eval', 'RLHF']
  },
  {
    id: 'j3',
    title: 'Senior NLP Engineer',
    company: 'Latimer Health',
    location: 'New York, NY · Remote',
    type: 'Full-time',
    score: 0.811,
    salary: '$195k–235k',
    experience: '5+ yrs',
    edu: 'MS preferred',
    matched: ['NLP', 'Transformers', 'PyTorch', 'Distillation'],
    missing: ['Clinical NLP', 'HIPAA', 'BioBERT']
  },
  {
    id: 'j4',
    title: 'ML Engineer, Ranking',
    company: 'Cohort',
    location: 'Remote',
    type: 'Full-time',
    score: 0.742,
    salary: '$170k–210k',
    experience: '4+ yrs',
    edu: 'BS/MS',
    matched: ['Ranking', 'PyTorch', 'MLOps', 'Kubernetes'],
    missing: ['Learning-to-rank', 'XGBoost', 'A/B testing']
  },
  {
    id: 'j5',
    title: 'Search Infrastructure Engineer',
    company: 'Mosaic',
    location: 'Seattle, WA',
    type: 'Full-time',
    score: 0.681,
    salary: '$160k–200k',
    experience: '4+ yrs',
    edu: 'BS CS',
    matched: ['FAISS', 'Vector databases', 'Python'],
    missing: ['Elasticsearch', 'Lucene', 'Java', 'Distributed systems']
  },
  {
    id: 'j6',
    title: 'AI Research Engineer',
    company: 'Quill Research',
    location: 'Boston, MA',
    type: 'Full-time',
    score: 0.612,
    salary: '$190k–240k',
    experience: '5+ yrs',
    edu: 'PhD required',
    matched: ['PyTorch', 'HuggingFace', 'Transformers'],
    missing: ['Diffusion', 'CUDA kernels', 'Triton', 'Published research']
  }
];

const MODELS = [
  { id: 'BAAI/bge-large-en-v1.5', name: 'BAAI/bge-large-en-v1.5', dims: 1024, recommended: true }
];

Object.assign(window, {
  SAMPLE_RESUME, SAMPLE_JD,
  MOCK_JOBS,
  MODELS,
});
