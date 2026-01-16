FROM python:3.12-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml .
COPY discount_decisioning/ ./discount_decisioning/

RUN uv pip install --system -e .

CMD ["bash"]
