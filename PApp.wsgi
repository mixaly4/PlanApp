import os
import sys

path='/Users/konstantinmikhaylov/PythonPractice/apps/PlanApp/PApp'

if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'PApp.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
