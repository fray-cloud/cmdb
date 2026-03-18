from abc import ABC, abstractmethod

from pydantic import BaseModel, ConfigDict


class Query(BaseModel):
    model_config = ConfigDict(frozen=True)


class QueryHandler[R](ABC):
    @abstractmethod
    async def handle(self, query: Query) -> R: ...
