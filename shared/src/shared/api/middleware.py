from uuid import uuid4

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


class TenantMiddleware(BaseHTTPMiddleware):
    HEADER = "X-Tenant-ID"

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        tenant_id = request.headers.get(self.HEADER)
        if tenant_id is None:
            return JSONResponse(
                status_code=400,
                content={
                    "type": "urn:cmdb:error:MissingTenant",
                    "title": "Missing Tenant",
                    "status": 400,
                    "detail": f"Header '{self.HEADER}' is required",
                },
            )
        request.state.tenant_id = tenant_id
        return await call_next(request)


class UserMiddleware(BaseHTTPMiddleware):
    HEADER = "X-User-ID"

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request.state.user_id = request.headers.get(self.HEADER)
        return await call_next(request)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    HEADER = "X-Correlation-ID"

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        correlation_id = request.headers.get(self.HEADER) or str(uuid4())
        request.state.correlation_id = correlation_id
        response = await call_next(request)
        response.headers[self.HEADER] = correlation_id
        return response
