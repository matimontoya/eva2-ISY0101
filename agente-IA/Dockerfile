FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY data ./data

ENV PYTHONPATH=/app/src

CMD ["python", "-m", "agente_ia"]
