FROM cmdb-base:prod
COPY services/ipam/ ./services/ipam/
RUN uv sync --frozen --no-dev --package cmdb-ipam
EXPOSE 8000
CMD ["uv", "run", "--package", "cmdb-ipam", "uvicorn", "ipam.interface.main:app", "--host", "0.0.0.0", "--port", "8000"]
