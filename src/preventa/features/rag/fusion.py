from collections.abc import Hashable, Sequence


def reciprocal_rank_fusion[ItemId: Hashable](
    rankings: Sequence[Sequence[ItemId]],
    *,
    k: int = 60,
) -> list[tuple[ItemId, float]]:
    """Fuse ordered result lists while retaining candidates unique to one retriever."""
    scores: dict[ItemId, float] = {}
    for ranking in rankings:
        for rank, item_id in enumerate(ranking, start=1):
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank)

    return sorted(scores.items(), key=lambda item: (-item[1], str(item[0])))
