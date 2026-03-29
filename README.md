# GovCore Django Template

Lean, government-grade Django template for building secure multi-tenant applications.

## Quick Start

See `.env.example` for configuration.

```bash
python manage.py migrate
python manage.py runserver
```

## Template Configuration

Use the interactive configurator to choose auth, API, and tenancy features:

```bash
make configure
```

Or run full setup with one short command:

```bash
make setup
```

Step-by-step setup commands:

```bash
make setup-configure
make setup-install
make setup-check
```

Equivalent aliases:

```bash
make setup-application
make aplication
```

This generates:

- `requirements/features.txt` (optional dependencies)
- `config/settings/features.py` (optional Django settings)
- `config/template_profile.json` (chosen options)

Run non-interactive mode in automation:

```bash
python scripts/configure_boilerplate.py \
  --non-interactive \
  --api yes \
  --auth jwt_oauth2 \
  --docs yes \
  --social-auth no \
  --mfa yes \
  --tenancy schema
```

Non-interactive setup via Make:

```bash
make setup SETUP_ARGS="--non-interactive --api yes --auth jwt_oauth2 --docs yes --social-auth no --mfa yes --tenancy schema"
```

**Endpoints:**

- Admin: <http://localhost:8000/admin/>
- API Swagger UI: <http://localhost:8000/api/docs/>
- API ReDoc: <http://localhost:8000/api/redoc/>
- OpenAPI Schema: <http://localhost:8000/api/schema/>

## Tech Stack

- **Django 5.x** core framework
- **PostgreSQL** first-class production database
- **Celery + Redis** async processing
- Optional features selected through setup: DRF, JWT, OAuth2, OpenAPI docs, MFA, social auth, schema tenancy

## Government-Grade Features

- Secure defaults (custom user model, session security settings)
- Pluggable authentication architecture
- Multi-tenant-ready model structure
- Repeatable setup flow for new projects

## License

Use this template according to your organization policy and add a project-specific license file in downstream repositories.
