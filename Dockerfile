FROM python:3.12-slim

WORKDIR /app

COPY jx3-jcl-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY Formulator/ /app/formulator/
COPY jx3-jcl-service/app/ /app/app/

ENV FORMULATOR_PATH=/app/formulator
ENV PYTHONPATH=/app

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--timeout-keep-alive", "30"]
