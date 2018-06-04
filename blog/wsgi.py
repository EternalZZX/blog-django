"""
WSGI config for blog project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/howto/deployment/wsgi/
"""

import os
PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))

import sys
sys.path.insert(0, PROJECT_DIR)

os.environ["DJANGO_SETTINGS_MODULE"] = "blog.settings"

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

import djcelery
djcelery.setup_loader()
