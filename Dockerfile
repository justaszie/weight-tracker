FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1, PYTHONUNBUFFERED=1

WORKDIR /project

RUN pip install --no-cache-dir poetry

COPY poetry.lock pyproject.toml ./

RUN poetry config virtualenvs.create false && poetry install --only main --no-root

COPY ./app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
