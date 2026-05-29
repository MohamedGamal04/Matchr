# Prototype — Streamlit / pickle version

> **Archived.** This folder holds the original Streamlit-based prototype the
> current Matchr stack grew out of. It is preserved as a portfolio artifact
> and is no longer the supported entry point.
> For the live stack (FastAPI + Supabase + React) see the [root README](../README.md).

Semantic search app to match resumes and job descriptions using
Sentence-Transformers and cosine similarity. Includes a Streamlit UI and a
notebook for data prep, profiling, and embedding generation.

Original demo: https://resume-screening-using-nlp-jepby5phpgkbpmokkzs3tc.streamlit.app/

## Features
- Semantic matching: resumes ↔ jobs via transformer embeddings
- Top-K results with similarity scores
- Skills-overlap extraction (simple NLP heuristic)
- Preprocessing pipeline (NLTK, contractions, lemmatization)
- Embeddings persisted as pickles under `model/`
- Streamlit UI with model selection and token-gated access

## Contents
- `app.py` — Streamlit UI for the three matching modes
- `ResumeScreeningUsingNLP.ipynb` — Data loading, preprocessing, profiling, and embedding generation
- `requirements.txt` — Python dependencies for this prototype
- `model/` — Saved artifacts (`job_embeddings.pkl`, `resume_embeddings.pkl`, `job_data.pkl`, `resume_data.pkl`)
- `reports/` — `ydata-profiling` HTML outputs from the notebook
- `examples/` — Sample resume (PDF / DOCX / TXT) and job description used during development
- `BACKEND_IMPLEMENTATION.md` — Spec written when moving from this prototype to the FastAPI backend

## Run it (Conda / Python 3.10)

```bash
conda create -n torch python=3.10 -y
conda activate torch
pip install -r requirements.txt
python -c "import nltk; [nltk.download(p) for p in ['punkt','averaged_perceptron_tagger','wordnet','omw-1.4','stopwords']]"
streamlit run app.py
```

You'll need a Hugging Face token (https://huggingface.co/settings/tokens) for
the model loader — the sidebar prompts for it.

## Datasets

- Resumes: https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset
- Jobs: https://www.kaggle.com/datasets/ravindrasinghrana/job-description-dataset
