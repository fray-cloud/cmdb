FROM cmdb-base:prod
COPY services/event/ ./services/event/
RUN uv sync --frozen --no-dev --package cmdb-event
EXPOSE 8000
CMD ["uv", "run", "--package", "cmdb-event", "uvicorn", "event.interface.main:app", "--host", "0.0.0.0", "--port", "8000"]
