from uuid import uuid4

import pytest

from preventa.features.rag.guardrails import (
    UngroundedSuggestionError,
    require_citations,
)
from preventa.features.rag.schemas import Candidate, Citation, GeneratedDraft


def test_rejects_empty_generation() -> None:
    with pytest.raises(UngroundedSuggestionError):
        require_citations(GeneratedDraft(candidates=[]))


def test_accepts_candidate_with_source_citation() -> None:
    chunk_id = uuid4()
    draft = GeneratedDraft(
        candidates=[
            Candidate(
                kind="safeguard",
                text="Independent high-pressure trip",
                confidence="medium",
                citations=[
                    Citation(
                        chunk_id=chunk_id,
                        source_ref="study:HAZOP-2024-018",
                        section_ref="Node 12",
                        excerpt="Independent trip listed for the same deviation.",
                    )
                ],
            )
        ]
    )

    require_citations(draft, allowed_chunk_ids={chunk_id})


def test_rejects_citation_outside_retrieved_context() -> None:
    draft = GeneratedDraft(
        candidates=[
            Candidate(
                kind="cause",
                text="Blocked discharge",
                confidence="low",
                citations=[
                    Citation(
                        chunk_id=uuid4(),
                        source_ref="invented",
                        excerpt="Not in retrieved context.",
                    )
                ],
            )
        ]
    )

    with pytest.raises(UngroundedSuggestionError):
        require_citations(draft, allowed_chunk_ids={uuid4()})
