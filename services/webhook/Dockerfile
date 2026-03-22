FROM cmdb-base:prod
COPY services/webhook/ ./services/webhook/
RUN uv sync --frozen --no-dev --package cmdb-webhook
EXPOSE 8000
CMD ["uv", "run", "--package", "cmdb-webhook", "uvicorn", "webhook.interface.main:app", "--host", "0.0.0.0", "--port", "8000"]
