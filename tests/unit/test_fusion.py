from preventa.features.rag.fusion import reciprocal_rank_fusion


def test_rrf_rewards_items_returned_by_both_retrievers() -> None:
    fused = reciprocal_rank_fusion(
        [
            ["dense-only", "shared", "tail"],
            ["shared", "sparse-only"],
        ],
        k=60,
    )

    assert fused[0][0] == "shared"
    assert {item_id for item_id, _ in fused} == {
        "dense-only",
        "shared",
        "tail",
        "sparse-only",
    }


def test_rrf_is_deterministic_for_tied_scores() -> None:
    fused = reciprocal_rank_fusion([["b"], ["a"]], k=60)

    assert [item_id for item_id, _ in fused] == ["a", "b"]

