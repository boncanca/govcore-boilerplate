# OAuth2 Integration Plan

## Goal

Keep OAuth2 optional in the template, and enable it only when projects need machine-to-machine authentication.

## Minimal Steps

1. Run setup with OAuth2 enabled.
2. Install dependencies.
3. Add OAuth2 URLs and scopes in the target application.
4. Protect selected endpoints with scope-based permissions.

## Example Scope Mapping

```python
OAUTH2_SCOPES = {
    "read": "Read protected resources",
    "write": "Write protected resources",
}
```

## References

- [Django OAuth Toolkit](https://django-oauth-toolkit.readthedocs.io/)
- [DOT + DRF](https://django-oauth-toolkit.readthedocs.io/en/latest/rest_framework/getting_started.html)
