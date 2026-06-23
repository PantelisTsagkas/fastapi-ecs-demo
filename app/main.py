from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

app = FastAPI(title="fastapi-ecs-demo", version="0.1.0")


class ItemIn(BaseModel):
    name: str
    description: str | None = None


class Item(ItemIn):
    id: UUID


# In-memory store. Fine for a demo; swap for DynamoDB/Postgres for anything real.
_items: dict[UUID, Item] = {}


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "fastapi-ecs-demo", "status": "ok"}


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
