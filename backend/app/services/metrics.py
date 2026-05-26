import math


# ── Information Retrieval metrics ────────────────────────────────────────────

def dcg_at_k(relevances: list[float], k: int) -> float:
    """Discounted Cumulative Gain at K."""
    return sum(
        rel / math.log2(rank + 2)
        for rank, rel in enumerate(relevances[:k])
    )


def ndcg_at_k(relevances: list[float], k: int) -> float:
    """
    Normalised DCG @ K.
    relevances[i] = 1.0 if relevant, 0.0 otherwise (binary judgements).
    Returns 0.0 when there are no relevant items.
    """
    ideal = sorted(relevances, reverse=True)
    idcg = dcg_at_k(ideal, k)
    return dcg_at_k(relevances, k) / idcg if idcg > 0 else 0.0


def mrr(relevances: list[float]) -> float:
    """Mean Reciprocal Rank — reciprocal of the rank of the first relevant item."""
    for i, rel in enumerate(relevances):
        if rel > 0:
            return 1.0 / (i + 1)
    return 0.0


def precision_at_k(relevances: list[float], k: int) -> float:
    """Fraction of top-K results that are relevant."""
    if k == 0:
        return 0.0
    return sum(1.0 for r in relevances[:k] if r > 0) / k


def recall_at_k(relevances: list[float], total_relevant: int, k: int) -> float:
    """Fraction of all relevant items found in the top K."""
    if total_relevant == 0:
        return 0.0
    return sum(1.0 for r in relevances[:k] if r > 0) / total_relevant


# ── Feedback-driven metric computation ───────────────────────────────────────

def compute_metrics_from_feedback(
    result_ids: list[str],
    feedback: dict[str, str],
) -> dict[str, float]:
    """
    Derive IR metrics from thumbs-up / clicked signals.

    Parameters
    ----------
    result_ids : ordered list of result UUIDs (as returned to the user)
    feedback   : {result_id: "up" | "down" | "clicked"}

    Returns
    -------
    dict with ndcg_at_5, mrr, precision_at_5
    """
    # "up" and "clicked" are treated as relevant; "down" is not.
    relevances = [
        1.0 if feedback.get(rid) in ("up", "clicked") else 0.0
        for rid in result_ids
    ]
    return {
        "ndcg_at_5":     round(ndcg_at_k(relevances, 5), 4),
        "mrr":           round(mrr(relevances), 4),
        "precision_at_5": round(precision_at_k(relevances, 5), 4),
    }
