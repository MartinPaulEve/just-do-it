import os

DJANGO_ENV = os.environ.get("DJANGO_ENV", "local")

if DJANGO_ENV == "production":
    from config.settings.production import *  # noqa: F401, F403
else:
    from config.settings.local import *  # noqa: F401, F403
