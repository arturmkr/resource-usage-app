FROM python:3.9-slim

RUN pip install pipenv

RUN apt-get update \
  && apt-get install -y --no-install-recommends libpq-dev python3-dev gcc \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock
RUN pipenv install --deploy --system --ignore-pipfile

COPY . /app

ENTRYPOINT [ "python3", "-m", "app" ]