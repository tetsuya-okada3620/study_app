FROM python:3.13-slim

COPY . .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["gunicorn", "run:app", "--bind", "0.0.0.0:10000"]