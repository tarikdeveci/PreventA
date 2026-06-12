from fastapi import APIRouter, HTTPException, status

from preventa.api.dependencies import DeviationAssistServiceDep
from preventa.features.rag.guardrails import UngroundedSuggestionError
from preventa.features.rag.schemas import DeviationAssistRequest, DeviationAssistResponse

router = APIRouter()


@router.post(
    "/deviation-assist",
    response_model=DeviationAssistResponse,
    status_code=status.HTTP_201_CREATED,
)
async def deviation_assist(
    payload: DeviationAssistRequest,
    service: DeviationAssistServiceDep,
) -> DeviationAssistResponse:
    try:
        return await service.assist(payload)
    except UngroundedSuggestionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "ungrounded_suggestion",
                "message": str(exc),
            },
        ) from exc

