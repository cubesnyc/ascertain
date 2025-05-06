FROM python:3.12

ENV PATH="/root/.local/bin:$PATH"

RUN mkdir /workspace
WORKDIR /workspace

RUN curl -sSL https://install.python-poetry.org | python3 -

COPY poetry.lock* pyproject.toml .

RUN poetry install --no-root

COPY . .

CMD ["poetry", "run", "uvicorn", "--host", "0.0.0.0", "--port", "8000", "src.api.app:app"]