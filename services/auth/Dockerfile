FROM cmdb-base:prod
COPY services/auth/ ./services/auth/
RUN uv sync --frozen --no-dev --package cmdb-auth
EXPOSE 8000
CMD ["uv", "run", "--package", "cmdb-auth", "uvicorn", "auth.interface.main:app", "--host", "0.0.0.0", "--port", "8000"]
