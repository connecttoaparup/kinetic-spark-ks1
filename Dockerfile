FROM python:3.11-slim
WORKDIR /app
COPY . /app
CMD ["echo", "Kinetic Spark (KS-1) is running!"]