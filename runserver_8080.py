import os
import sys
from django.core.management import execute_from_command_line

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Core.settings")

execute_from_command_line([
    sys.argv[0],
    "runserver",
    "0.0.0.0:8080"
])

