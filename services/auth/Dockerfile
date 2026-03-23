FROM cmdb-base:prod
COPY services/auth/ ./services/auth/
RUN uv sync --frozen --no-dev --package cmdb-auth
EXPOSE 8000
CMD ["uv", "run", "--package", "cmdb-auth", "uvicorn", "auth.main:app", "--host", "0.0.0.0", "--port", "8000"]
