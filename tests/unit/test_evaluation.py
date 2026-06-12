from scripts.evaluate_retrieval import citation_accuracy, recall_at_k


def test_recall_at_k() -> None:
    assert recall_at_k({"a", "b"}, ["a", "x", "b"], 2) == 0.5


def test_citation_accuracy() -> None:
    assert citation_accuracy({"a", "b"}, ["a", "invented"]) == 0.5

