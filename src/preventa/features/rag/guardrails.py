from collections.abc import Collection
from uuid import UUID

from preventa.features.rag.schemas import GeneratedDraft


class UngroundedSuggestionError(ValueError):
    pass


def require_citations(
    draft: GeneratedDraft,
    *,
    minimum: int = 1,
    allowed_chunk_ids: Collection[UUID] | None = None,
) -> None:
    if not draft.candidates:
        raise UngroundedSuggestionError("The model returned no candidates.")

    for candidate in draft.candidates:
        if len(candidate.citations) < minimum:
            raise UngroundedSuggestionError(
                f"{candidate.kind} candidate does not meet the citation requirement."
            )
        if allowed_chunk_ids is not None:
            invalid_ids = {
                citation.chunk_id
                for citation in candidate.citations
                if citation.chunk_id not in allowed_chunk_ids
            }
            if invalid_ids:
                raise UngroundedSuggestionError(
                    f"{candidate.kind} candidate cites chunks outside the retrieved context."
                )
