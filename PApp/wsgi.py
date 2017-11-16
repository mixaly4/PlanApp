"""
WSGI config for PApp project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/howto/deployment/wsgi/
"""

python_home = '/Users/konstantinmikhaylov/PythonPractice/apps/PlanApp/env'

import os, sys
sys.path.append('/Users/konstantinmikhaylov/PythonPractice/apps/PlanApp/PApp')
sys.path.append('/Users/konstantinmikhaylov/PythonPractice/apps/PlanApp/PApp/PApp')

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "PApp.settings")

application = get_wsgi_application()
