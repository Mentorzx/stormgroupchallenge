from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import Settings, get_db, get_settings
from app.application.services.breach_sync_service import BreachSyncService
from app.infrastructure.hibp.client import HIBPClient
from app.infrastructure.persistence.repositories import BreachRepository
from app.schemas.breach import SyncResponse

router = APIRouter(tags=["sync"])


@router.post("/sync", response_model=SyncResponse)
def sync_breaches(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> SyncResponse:
    client = HIBPClient(
        url=settings.hibp_breaches_url,
        user_agent=settings.hibp_user_agent,
        timeout_seconds=settings.hibp_timeout_seconds,
    )
    service = BreachSyncService(client=client, repository=BreachRepository(db))
    return SyncResponse.model_validate(service.sync())
