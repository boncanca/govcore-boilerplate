# Template Use Guide

Use this repository as a starting point for secure, backend-first Django applications.

## 1. Create Your Project

Create a new repository from this template and clone it locally.

## 2. Configure Environment

Copy `.env.example` to `.env` and fill in required values:

- `SECRET_KEY`
- `DATABASE_URL`
- `REDIS_URL`

## 3. Select Features

Run one of the setup flows:

```bash
make setup
```

Or automate with explicit options:

```bash
make setup SETUP_ARGS="--non-interactive --api yes --auth jwt_oauth2 --docs yes --social-auth no --mfa yes --tenancy none"
```

This generates:

- `requirements/features.txt`
- `config/settings/features.py`
- `config/template_profile.json`

## 4. Run Locally

```bash
python manage.py migrate
python manage.py runserver
```

## 5. Quality Gates

Run before pushing changes:

```bash
make lint
make check
make test
```

GitHub Actions CI in `.github/workflows/ci.yml` runs equivalent checks on pushes and pull requests.
