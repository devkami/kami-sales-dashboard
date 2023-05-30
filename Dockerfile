FROM python:3.9-slim as python
LABEL maintainer="dev@kamico.com.br"
ENV PYTHONUNBUFFERED=true
ENV PIP_DISABLE_VERSION_CHECK=1

WORKDIR /kami_sales_dashboard
FROM python as poetry
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VIRTUALENVS_IN_PROJECT=true
ENV PATH="$POETRY_HOME/bin:$PATH"
RUN python -c 'from urllib.request import urlopen; print(urlopen("https://install.python-poetry.org").read().decode())' | python -
COPY . ./
RUN poetry install --only main --no-interaction --no-ansi -vvv


FROM python as runtime
ENV PATH="/kami_sales_dashboard/.venv/bin:$PATH"
COPY --from=poetry /kami_sales_dashboard /kami_sales_dashboard

EXPOSE 8005
ENTRYPOINT ["python", "kami_sales_dashboard/app.py"]