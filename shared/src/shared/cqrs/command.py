from abc import ABC, abstractmethod

from pydantic import BaseModel, ConfigDict


class Command(BaseModel):
    model_config = ConfigDict(frozen=True)


class CommandHandler[R](ABC):
    @abstractmethod
    async def handle(self, command: Command) -> R: ...
