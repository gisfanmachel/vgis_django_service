pyc编译：

1）修改配置文件config.json
2）执行init_dir.py，自动创建目录
3）在上述目录的source目录下（比如E:\complie\zxbcfzcd_complie\3.9\source），手动方式git clone下载代码 https://106.13.81.105:8443/r/baoxian_ocr_service.git，这里为具体项目的git地址
4) 执行update_pyc/pyd_complie_package.py,编译整个项目代码

上述方法会将py源文件编译成pyc/pyd文件，但全局配置文件 setting.py仍保留， 以便修改为用户现场参数

如果static目录下有资源文件或数据等，需要手动拷贝到相应位置

启动项目
python manage.pyc/pyd runserver  0.0.0.0:8683

