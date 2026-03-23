import hashlib
import secrets

from shared.cqrs.command import Command, CommandHandler
from shared.domain.exceptions import EntityNotFoundError
from shared.messaging.producer import KafkaEventProducer

from auth.api_token.domain.api_token import APIToken
from auth.api_token.domain.repository import APITokenRepository
from auth.api_token.query.dto import APITokenDTO


class CreateAPITokenHandler(CommandHandler[APITokenDTO]):
    def __init__(
        self,
        repository: APITokenRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._repository = repository
        self._event_producer = event_producer

    async def handle(self, command: Command) -> APITokenDTO:
        raw_key = secrets.token_urlsafe(48)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        token = APIToken.create(
            user_id=command.user_id,
            tenant_id=command.tenant_id,
            key_hash=key_hash,
            description=command.description,
            scopes=command.scopes,
            expires_at=command.expires_at,
            allowed_ips=command.allowed_ips,
        )

        await self._repository.save(token)

        for event in token.collect_events():
            await self._event_producer.publish("auth.events", event)

        return APITokenDTO(
            id=token.id,
            user_id=token.user_id,
            tenant_id=token.tenant_id,
            description=token.description,
            scopes=token.scopes,
            expires_at=token.expires_at,
            allowed_ips=token.allowed_ips,
            is_revoked=token.is_revoked,
            created_at=token.created_at,
            key=raw_key,
        )


class RevokeAPITokenHandler(CommandHandler[None]):
    def __init__(
        self,
        repository: APITokenRepository,
        event_producer: KafkaEventProducer,
    ) -> None:
        self._repository = repository
        self._event_producer = event_producer

    async def handle(self, command: Command) -> None:
        token = await self._repository.find_by_id(command.token_id)
        if token is None:
            raise EntityNotFoundError(f"API Token {command.token_id} not found")

        token.revoke()
        await self._repository.save(token)

        for event in token.collect_events():
            await self._event_producer.publish("auth.events", event)
