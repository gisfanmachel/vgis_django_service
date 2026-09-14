import os

from django.apps import AppConfig
from my_project import settings

class MyAppConfig(AppConfig):
    name = 'my_app'
    # 验证码字体文件路径
    verification_font_path = os.path.join(settings.STATICFILES_DIRS[0], "font", "COOPBL.TTF")

    def ready(self):
        # 注册 system check（分模块路由前缀冲突校验等），
        # manage.py check 与 runserver 启动时都会跑
        from my_app import checks  # noqa: F401