FROM python:3.11-alpine

WORKDIR /app

RUN apk add --no-cache wget

RUN addgroup -S appgroup && \
    adduser -S -G appgroup appuser


COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

USER appuser

ENV APP_PORT=3000
EXPOSE ${APP_PORT}

CMD ["/bin/sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${APP_PORT}"]

