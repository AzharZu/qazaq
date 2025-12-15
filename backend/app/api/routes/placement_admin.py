from copy import deepcopy
from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException, status

from ...services.placement_service import PLACEMENT_SECTIONS

router = APIRouter(prefix="/api/placement/admin", tags=["placement-admin"])

# In-memory store seeded from placement_service
_store: List[Dict[str, Any]] = []


def _seed():
    global _store
    if _store:
        return
    flat = []
    for section in PLACEMENT_SECTIONS:
        for q in section["questions"]:
            flat.append(
                {
                    "id": q["id"],
                    "question": q["question"],
                    "answers": {"options": q["options"], "correct": q["correct"]},
                    "level": section.get("title") or section.get("key"),
                }
            )
    _store = flat


@router.get("")
def list_questions():
    _seed()
    return deepcopy(_store)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_question(payload: Dict[str, Any]):
    _seed()
    if not payload.get("id"):
        payload["id"] = f"custom_{len(_store)+1}"
    _store.append(payload)
    return payload


@router.put("/{qid}")
def update_question(qid: str, payload: Dict[str, Any]):
    _seed()
    for idx, item in enumerate(_store):
        if str(item.get("id")) == qid:
            _store[idx] = {**item, **payload, "id": qid}
            return _store[idx]
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")


@router.delete("/{qid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(qid: str):
    _seed()
    for idx, item in enumerate(_store):
        if str(item.get("id")) == qid:
            _store.pop(idx)
            return
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
