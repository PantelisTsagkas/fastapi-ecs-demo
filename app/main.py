from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="fastapi-ecs-demo", version="0.1.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class ItemIn(BaseModel):
    name: str
    description: str | None = None


class Item(ItemIn):
    id: UUID


# In-memory store. Fine for a demo; swap for DynamoDB/Postgres for anything real.
_items: dict[UUID, Item] = {}


@app.get("/")
def root() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    """Used by the ECS task health check and the ALB target group."""
    return {"status": "healthy"}


@app.get("/items", response_model=list[Item])
def list_items() -> list[Item]:
    return list(_items.values())


@app.post("/items", response_model=Item, status_code=status.HTTP_201_CREATED)
def create_item(item_in: ItemIn) -> Item:
    item = Item(id=uuid4(), **item_in.model_dump())
    _items[item.id] = item
    return item


@app.get("/items/{item_id}", response_model=Item)
def get_item(item_id: UUID) -> Item:
    item = _items.get(item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )
    return item
