FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /workspace/backend/services/vector-service

RUN pip install --upgrade pip
COPY services/vector-service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY services/vector-service/app ./app
COPY services/vector-service/app /D/Projects/Sutr/Sutr/backend/services/vector-service/app

EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
