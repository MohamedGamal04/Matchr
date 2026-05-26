from pydantic import BaseModel, Field
from typing import Optional


# ── Match request/response schemas ────────────────────────────────────────────

class MatchRequest(BaseModel):
    text: str = Field(..., min_length=10, description="Resume or job description text")
    model_name: str = Field("BAAI/bge-large-en-v1.5", description="Bi-encoder model to use")
    top_k: int = Field(5, ge=1, le=50, description="Number of results to return")
    rerank: bool = Field(True, description="Whether to apply cross-encoder reranking")


class JobResult(BaseModel):
    job_id: str
    similarity: float
    rerank_score: Optional[float] = None
    title: str
    company: str
    salary: str
    experience: str
    work_type: str
    skills: list[str]
    matched_skills: list[str] = []
    missing_skills: list[str] = []
    source: str = ""


class ResumeResult(BaseModel):
    resume_id: str
    similarity: float
    rerank_score: Optional[float] = None
    category: str
    preview: str
    matched_skills: list[str] = []
    missing_skills: list[str] = []
    source: str = ""


class MatchResponse(BaseModel):
    results: list[JobResult] | list[ResumeResult]
    model_used: str
    reranked: bool
    elapsed_ms: int
    eval_id: Optional[str] = None


class OneToOneRequest(BaseModel):
    job_text: str = Field(..., min_length=10)
    resume_text: str = Field(..., min_length=10)
    model_name: str = "BAAI/bge-large-en-v1.5"


class OneToOneResponse(BaseModel):
    similarity: float
    quality: str          # "Excellent" | "Very Good" | "Good" | "Fair" | "Poor"
    matched_skills: list[str]
    job_skills: list[str]
    resume_skills: list[str]


# ── Evaluation schemas ────────────────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    eval_id: str
    result_id: str
    action: str = Field(..., pattern="^(up|down|clicked)$")


class FeedbackResponse(BaseModel):
    status: str


# ── Ingest schemas ────────────────────────────────────────────────────────────

class IngestResumeRequest(BaseModel):
    category: str = Field(..., min_length=2, max_length=80)
    full_text: str = Field(..., min_length=50, max_length=20000)


class IngestJobRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=120)
    company: Optional[str] = Field(None, max_length=120)
    salary: Optional[str] = Field(None, max_length=80)
    experience: Optional[str] = Field(None, max_length=80)
    work_type: Optional[str] = Field(None, max_length=40)
    skills: list[str] = Field(default_factory=list)
    full_text: str = Field(..., min_length=50, max_length=20000)


class IngestResponse(BaseModel):
    id: str
    source_id: str
    message: str
