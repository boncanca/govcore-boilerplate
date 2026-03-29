.PHONY: install run test lint format migrate shell configure setup setup-application aplication setup-configure setup-install setup-check check

SETUP_ARGS ?=

install:
	uv pip install -r requirements/local.txt

configure:
	python scripts/configure_boilerplate.py $(SETUP_ARGS)

setup: setup-configure setup-install setup-check

setup-application: setup

# Alias for common typo
aplication: setup

setup-configure:
	python scripts/configure_boilerplate.py $(SETUP_ARGS)

setup-install:
	uv pip install -r requirements/local.txt

setup-check:
	python manage.py check

check: setup-check

run:
	python manage.py runserver

migrate:
	python manage.py makemigrations
	python manage.py migrate

test:
	DJANGO_SETTINGS_MODULE=config.settings.test pytest

lint:
	ruff check .

format:
	ruff format .

shell:
	python manage.py shell_plus

worker:
	celery -A tasks.celery worker --loglevel=info
