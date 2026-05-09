FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /workspace/backend/services/upload-service

RUN pip install --upgrade pip
COPY services/upload-service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY services/upload-service/app ./app
COPY services/upload-service/app /D/Projects/Sutr/Sutr/backend/services/upload-service/app

VOLUME ["/workspace/backend/services/upload-service/uploads"]
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
