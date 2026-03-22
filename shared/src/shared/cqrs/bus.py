from typing import Any

from shared.cqrs.command import Command, CommandHandler
from shared.cqrs.query import Query, QueryHandler


class CommandBus:
    def __init__(self) -> None:
        self._handlers: dict[type[Command], CommandHandler[Any]] = {}

    def register(self, command_type: type[Command], handler: CommandHandler[Any]) -> None:
        if command_type in self._handlers:
            raise ValueError(f"Handler already registered for {command_type.__name__}")
        self._handlers[command_type] = handler

    async def dispatch(self, command: Command) -> Any:
        handler = self._handlers.get(type(command))
        if handler is None:
            raise ValueError(f"No handler registered for {type(command).__name__}")
        return await handler.handle(command)


class QueryBus:
    def __init__(self) -> None:
        self._handlers: dict[type[Query], QueryHandler[Any]] = {}

    def register(self, query_type: type[Query], handler: QueryHandler[Any]) -> None:
        if query_type in self._handlers:
            raise ValueError(f"Handler already registered for {query_type.__name__}")
        self._handlers[query_type] = handler

    async def dispatch(self, query: Query) -> Any:
        handler = self._handlers.get(type(query))
        if handler is None:
            raise ValueError(f"No handler registered for {type(query).__name__}")
        return await handler.handle(query)
