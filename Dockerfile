FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ARG DJANGO_SECRET_KEY_BUILD
ENV DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY_BUILD}

ARG DJANGO_DEBUG_BUILD
ENV DJANGO_DEBUG=${DJANGO_DEBUG_BUILD}

ARG DJANGO_ALLOWED_HOSTS_BUILD
ENV DJANGO_ALLOWED_HOSTS=${DJANGO_ALLOWED_HOSTS_BUILD}

COPY . .

RUN python manage.py migrate
RUN python manage.py add_default_categories

# Create a non-root user
RUN adduser --disabled-password --gecos '' admin
RUN chown -R admin:admin /app  # user:group
USER admin

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "django_project.wsgi:application"]
