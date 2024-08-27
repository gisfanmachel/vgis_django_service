pyc编译：

1）修改配置文件config.json
2）执行init_dir.py，自动创建目录
3）在上述目录的source目录下
    E:\complie\zxbcfzcd_complie\3.9\source 或  /root/cxw/complie/cysxydai_complie/3.8/source
    手动方式git clone下载代码  git clone https://chenxw:****@106.13.81.105:8443/r/cysxydai_service.git，这里为具体项目的git地址
4) 执行update_pyc/pyd_complie_package.py,编译整个项目代码

上述方法会将py源文件编译成pyc/pyd文件，但全局配置文件 setting.py仍保留， 以便修改为用户现场参数

如果static目录下有资源文件或数据等，需要手动拷贝到相应位置

启动项目
E:\ProgramData\miniconda3\envs\geodjango\python.exe E:\complie\cysxydai_complie\3.10\complie_pyd\cysxydai_service\manage.pyc runserver 0.0.0.0:10789

