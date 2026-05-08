#!/bin/bash

# -- master test runner script to ensure 95% coverage across all services --

SERVICES=(
  "upload-service"
  "processing-service"
  "vector-service"
  "chat-service" 
  "summary-service"
  "media-service"
  "api-gateway"
)

for SERVICE in "${SERVICES[@]}"
do
  echo "========================================="
  echo "🧪 Running tests for $SERVICE..."
  echo "========================================="
  cd backend/services/$SERVICE
  
  # -- FIX: Added PYTHONPATH=. so pytest knows where the 'app' module is --
  PYTHONPATH=. pytest tests/ --cov=app --cov-report=term-missing --cov-fail-under=95
  
  if [ $? -ne 0 ]; then
    echo "❌ Tests failed for $SERVICE or coverage is below 95%!"
    exit 1
  fi
  cd ../../../
done

echo "✅ All services passed successfully with >=95% coverage."