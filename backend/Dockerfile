FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Railway injects PORT env variable
ENV PORT=8080
EXPOSE $PORT

CMD gunicorn --bind 0.0.0.0:$PORT server:app
