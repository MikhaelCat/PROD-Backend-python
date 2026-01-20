FROM python:3.11-slim


ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        curl \          
    && rm -rf /var/lib/apt/lists/*

COPY solution/requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY ./requirements.txt requirements.txt
COPY ./api ./api
COPY ./auth ./auth
COPY ./database ./database
COPY ./dsl ./dsl
COPY ./models ./models
COPY ./main.py main.py


RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8080

# Run the application
CMD ["uvicorn", "solution.main:app", "--host", "0.0.0.0", "--port", "8080"]