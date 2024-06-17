import os

from django.apps import AppConfig
from my_project import settings

class MyAppConfig(AppConfig):
    name = 'my_app'
    # 验证码字体文件路径
    verification_font_path = os.path.join(settings.STATICFILES_DIRS[0], "font", "COOPBL.TTF")