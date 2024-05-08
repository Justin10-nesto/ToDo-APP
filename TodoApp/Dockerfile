FROM python:3.9-alpine

ENV PYTHONUNBUFFERED 1   
WORKDIR /app

COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . /app/

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "TodoApp.wsgi:application"]
