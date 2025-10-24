# 1) File: shop/context_processors.py
# create this new file at: <project_root>/shop/context_processors.py
from django.conf import settings

def site_settings(request):
    """
    Inject site-level settings needed by templates.
    Exposes:
      - settings: the Django settings module (read-only usage in templates)
      - company_name: shortcut for templates
    """
    return {
        "settings": settings,
        "company_name": getattr(settings, "COMPANY_NAME", "ragul solutions"),
    }
