FROM cmdb-base:prod
COPY services/tenant/ ./services/tenant/
RUN uv sync --frozen --no-dev --package cmdb-tenant
EXPOSE 8000
CMD ["uv", "run", "--package", "cmdb-tenant", "uvicorn", "tenant.interface.main:app", "--host", "0.0.0.0", "--port", "8000"]
