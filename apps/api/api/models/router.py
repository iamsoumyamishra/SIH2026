"""Model endpoints (AGENTS.md §29: models).

Lists configured local models and their live availability against Ollama.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db.models import Model as ModelRow
from db.session import get_db
from models.registry import get_registry
from security import auth

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("")
async def list_models(
    current=Depends(auth.get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    registry = get_registry()
    availability = await registry.availability()
    models = [
        {
            "id": a.info.id,
            "model": a.info.model_name,
            "provider": a.info.provider,
            "capabilities": list(a.info.capabilities),
            "vision_support": a.info.vision_support,
            "tool_support": a.info.tool_support,
            "embedding_support": a.info.embedding_support,
            "available": a.available,
            "error": a.error,
        }
        for a in availability
    ]
    # mirror into the models table so it is queryable (race-safe upsert)
    for a in availability:
        row = db.query(ModelRow).filter(ModelRow.name == a.info.model_name).first()
        if row is None:
            row = ModelRow(
                name=a.info.model_name,
                provider=a.info.provider,
                capabilities=list(a.info.capabilities),
                vision_support=a.info.vision_support,
                tool_support=a.info.tool_support,
            )
            db.add(row)
    try:
        db.commit()
    except IntegrityError:
        # Concurrent request inserted the same model rows; treat as already present.
        db.rollback()
    return {"models": models}


@router.post("/test")
async def test_model(
    model: str = "general",
    current=Depends(auth.get_current_user),
) -> dict:
    registry = get_registry()
    info = None
    for a in await registry.availability():
        if a.info.id == model or a.info.model_name == model:
            info = a
            break
    if info is None:
        return {"model": model, "available": False, "error": "Model not configured"}
    return {
        "model": info.info.model_name,
        "role": info.info.id,
        "available": info.available,
        "error": info.error,
    }
