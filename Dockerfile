FROM python:3.9-slim

RUN pip install --upgrade pip

RUN pip install pipenv

WORKDIR /app
COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock
RUN pipenv install --deploy --system --ignore-pipfile

COPY . /app

RUN chmod +x ./entrypoint.sh

ENTRYPOINT [ "./entrypoint.sh" ]