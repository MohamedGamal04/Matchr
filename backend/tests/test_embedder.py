"""Unit tests for embedder.rerank truncation fix."""
from unittest.mock import MagicMock, patch


def test_rerank_passes_full_text_to_cross_encoder():
    """Verify rerank does NOT truncate candidate text to 512 chars."""
    long_text = "python " * 500  # 3500+ chars, well over old 512 char limit

    fake_cross = MagicMock()
    fake_cross.predict.return_value = [0.9]

    with patch("app.services.embedder.get_crossencoder", return_value=fake_cross):
        from app.services.embedder import rerank
        candidates = [{"id": "r1", "full_text": long_text, "similarity": 0.8}]
        rerank("python developer", candidates, text_key="full_text", top_k=1)

    # The pair passed to predict should contain the FULL text
    call_args = fake_cross.predict.call_args[0][0]  # list of (query, doc) pairs
    assert len(call_args[0][1]) > 512, "full_text should not be truncated to 512 chars"
