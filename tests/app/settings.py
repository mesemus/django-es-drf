import os

from elasticsearch_dsl import connections

DEBUG = True
SECRET_KEY = "changeme"

ROOT_URLCONF = "tests.app.urls"

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django_es_drf",
    "tests.app",
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(PROJECT_DIR, "test.sqlite3"),
    }
}

connections.configure(default={"hosts": ["http://127.0.0.1:9200"]})
