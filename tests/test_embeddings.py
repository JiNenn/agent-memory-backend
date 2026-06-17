from app.embeddings import embed_text


def test_embed_text_is_deterministic_and_normalized() -> None:
    first = embed_text("Kubernetes volume permission", dimensions=32)
    second = embed_text("Kubernetes volume permission", dimensions=32)

    assert first == second
    assert len(first) == 32
    assert abs(sum(value * value for value in first) - 1.0) < 0.000001


def test_embed_text_rejects_invalid_dimensions() -> None:
    try:
        embed_text("text", dimensions=0)
    except ValueError as exc:
        assert "dimensions" in str(exc)
    else:
        raise AssertionError("expected ValueError")

