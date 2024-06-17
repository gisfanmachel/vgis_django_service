#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

from my_project import settings
from my_project.settings import APP_NAME, PROJECT_NAME


# 初始化环境
def init_env():
    dir_name_list = ["doc", "upload", "xls", "zip", "pdf", "file", "geojson"]
    for dir_name in dir_name_list:
        dir_path = os.path.join(str(settings.BASE_DIR),
                                "{}{}{}".format(APP_NAME,
                                    settings.STATIC_URL, dir_name))
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', '{}.settings'.format(PROJECT_NAME))
    init_env()
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
