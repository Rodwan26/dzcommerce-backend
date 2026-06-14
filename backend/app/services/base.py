import uuid
from typing import Any, Generic, TypeVar

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseService(Generic[ModelType]):
    def __init__(self, model: type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, id: uuid.UUID) -> ModelType:
        result = await self.db.execute(select(self.model).where(self.model.id == id))
        obj = result.scalar_one_or_none()
        if not obj:
            raise NotFoundException(self.model.__name__)
        return obj

    async def get_multi(
        self, *, skip: int = 0, limit: int = 100, filters: dict[str, Any] | None = None
    ) -> list[ModelType]:
        query = select(self.model)
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs) -> ModelType:
        obj = self.model(**kwargs)
        self.db.add(obj)
        await self.db.flush()
        return obj

    async def update(self, id: uuid.UUID, **kwargs) -> ModelType:
        obj = await self.get(id)
        for key, value in kwargs.items():
            if value is not None and hasattr(obj, key):
                setattr(obj, key, value)
        await self.db.flush()
        return obj

    async def delete(self, id: uuid.UUID) -> None:
        obj = await self.get(id)
        await self.db.delete(obj)
        await self.db.flush()

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        query = select(func.count()).select_from(self.model)
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)
        result = await self.db.execute(query)
        return result.scalar() or 0
