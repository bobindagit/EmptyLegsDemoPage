FROM python:3.10.0
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /working/EmptyLegsDemoPage
COPY /core /working/EmptyLegsDemoPage

RUN apt-get update -qq && apt-get install -y -qq
RUN pip install --upgrade pip
RUN apt-get install gdal-bin -y --fix-missing

COPY requirements.txt /working/EmptyLegsDemoPage/
RUN pip install --no-cache-dir -r /working/EmptyLegsDemoPage/requirements.txt

RUN python manage.py makemigrations
RUN python manage.py migrate
RUN python manage.py collectstatic --no-input