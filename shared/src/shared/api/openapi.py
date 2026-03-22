from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def customize_openapi(
    app: FastAPI,
    title: str,
    version: str,
    description: str = "",
) -> None:
    def custom_schema() -> dict:
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(
            title=title,
            version=version,
            description=description,
            routes=app.routes,
        )
        app.openapi_schema = schema
        return schema

    app.openapi = custom_schema  # type: ignore[method-assign]
