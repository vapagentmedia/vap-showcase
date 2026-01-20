# VAP MCP Server
FROM python:3.11-slim

WORKDIR /app

# Install vap-mcp package
RUN pip install --no-cache-dir vap-mcp

# Expose MCP endpoint
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import vap_mcp; print('OK')" || exit 1

# Run MCP server
CMD ["python", "-m", "vap_mcp"]
