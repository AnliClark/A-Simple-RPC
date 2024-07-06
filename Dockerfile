FROM python:3.10-slim
COPY . /app/
WORKDIR /app
CMD ["python", "app.py"]