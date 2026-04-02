from config.settings.base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS += [  # noqa: F405
    "debug_toolbar",
]

MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405

INTERNAL_IPS = [
    "127.0.0.1",
    "172.0.0.0/8",
]

# django-debug-toolbar needs this for Docker
import socket  # noqa: E402

hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
INTERNAL_IPS += [".".join(ip.split(".")[:-1] + ["1"]) for ip in ips]
