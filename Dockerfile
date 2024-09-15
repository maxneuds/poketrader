FROM python:3.12-slim

WORKDIR /app
COPY . /app

RUN pip install poetry
RUN poetry install --no-interaction --no-root

EXPOSE 42069

CMD [ "sh", "run.sh" ]


