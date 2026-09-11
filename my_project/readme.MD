

# 1.部署说明
## 1.1 主要包安装
>django安装最新包，完整包见requirements.txt
## 1.2 license包下载
>pip install license-authorize==1.0.4 -i https://pypi.python.org/simple/

---
# 2.django说明
[django官网](https://www.djangoproject.com/)
## 2.1新建项目 
>django-admin startproject my_project

## 2.2新建app 

>python manage.py startapp my_app


## 2.3 数据库更新
### 2.3.1 models类修改后，同步数据库
>python manage.py makemigrations<br>
>python manage.py migrate

### 2.3.2或者已有数据库，同步 models类
>python manage.py inspectdb<br>
>python manage.py inspectdb >my_app/models2.py

### 2.4 代码结构
> 共用urls类型
> 写自己的seririlzer类、models类、view类、manage类、utils类
> 

## 2.5启动服务 
> 通过django的runserver启动
> python manage.py runserver 0.0.0.0:10876  无数字证书启动
> python manage.py runserver_plus --cert server.crt 0.0.0.0:10876  有数字证书启动
> python manage.py runsslserver --certificate server.crt --key server.key 0.0.0.0:10876
> 
> 通过waitress启动
> https://docs.pylonsproject.org/projects/waitress/en/stable/runner.html
> 代码方式
> python run.py
> 命令行方式
> waitress-serve --port=10876--host=0.0.0.0 --threads=8 my_project.wsgi:application
> 启动后会在后台产生一个waitress进程
> 
> nginx方式
> 启动多个django服务(不同的端口)
> 然后通过nginx进行负载均衡
---

# 3.定制说明

>* 已包含了基础的用户信息表<br>
>* 定制修改my_project,my_app,my_static,my_api为自己需要的项目信息
>* 设计好数据库模型，导出sql语句 定义自增长主键，生成数据库
>* 通过代码自动生成器生成相关model,view,serializer等代码片段
>* 数据表录入一条初始化数据
>* 通过代码自动生成器生成postman测试用例，并将里面的/api/和"api"更新的的自己的

---
# 4.已扩展
>* 增加了自定义的日志类<br>
>* 增加了自定义的token授权类，token过期时间<br>
>* 增加了软件试用license控制<br>
>* 增加了长时间未登录的自动退出
>* 增加了多处登录的提示，只允许一处登录
>* 增加了强制登录
>* 实现了增加，更新，删除等view的重载
>* 增加了请求参数解密，响应结果加密功能
>* 增加登录密码失败次数过多后的锁定功能，指定时间后解锁
>* 增加了是否开启验证码功能
>* 增加Token-key的配置
>* 增加并发访问waitress
>* 增加代码pyc批量编译
>* 增加代码pyd批量编译
>* 增加django postgis支持 ，可以注释掉--去掉gis等组件
>* 增加 websocket 使用websocket 需要熟读websocket 的文档，理解原理，下面有一个案例https://blog.csdn.net/weixin_62935305/article/details/125422933
>* 因为websocket 需要配合redis缓存使用，所有增加了redis缓存链接 
>* 授权文件配置到代码目录外部
>* 存储高频访问的数据：利用Redis进行高效缓存
>* 增加多线程
>* 增加了对配置文件中的引用key(用于加密算法)的生成，及对代码引用的第三方appkey的加解密
>* 增加了自定义response类
>* 对相关配置进行了数据表存储，通过系统管理的参数配置进行控制
>* 支持多个model,多个viewer,多个serializer
>* 可配置多个路由
>* 增加雪花ID(15位,不超过前端支持的最长数字)
>* 增加celery异步任务   celery -A my_project worker -l info
>* >* 启动
>** celery -A my_project worker -l info
>*  监测
>** celery -A my_project inspect active
>*  查看
>** celery -A my_project flower --port=29613
>** http://192.168.31.39:29613 查看
>*  停止
>** celery multi stop w1 -A my_project -l info
>* 增加分页查询
>* 增加本地化语言支持(中文，英文等)：`my_app/enum/localization_enum.py` 为 CH/EN 成对的中英文字典，
>  请求头带 `Localization: CH / EN` 即可切换提示语；`CommonHelper.get_local_str(KEY, request)`
>* 增加统一的 ViewSet 基类 `my_app/views/custom.py::CustomModelViewSet`，
>  把 list/retrieve/destroy 的返回收敛成 Result 结构并自动按语言返回提示
>* 增加忘记密码（密保问题验证 + 一次性 userkey 重置密码）接口
>* 增加跨系统免登（A 系统登录后的 token 直接在 B 系统换登录态）与 token 有效性校验接口

---
# 5.待优化:
>+ 提高代码执行效率：稳定大数据量逻辑用c/c++写，cpython处理代码转换 
>+ 利用ElasticSearch进行全文检索
>+ 支持数据库存储过程的调用，数据库事务
>+ 支持异步调用
>+ 静态文件服务单独抽出来
>+ 内存优化：禁止垃圾回收来优化内存使用率
>+ 使用异步任务，将耗时的任务转换为异步任务，避免阻塞主线程，比如Celery和Dramatiq；Gearman 执行推送通知和异步任务
>+ 优化数据库访问：优化查询，模板缓存，查询缓存，Pgbouncer进行数据库连接池化,支撑分布式数据库。
>+ 数据备份：Postgres 和 Redis 都在主副本设置中运行，并使用EBS（弹性块存储）快照来频繁备份系统。>+ 
>+ 代码执行监控：Sentry 实时监控 Python 错误 Pingdom 用于外部服务监控，PagerDuty 用于处理事件和通知。
>+ 使用cdn加速静态资源的传输，减轻服务器的负载
>+ 调整服务器配置：使用负载均衡(nginx,haproxy)分发请求


---
# 6.说明
> 支持python3.8,3.9,3.10
> 支持django3.*,4.*
 
---
# 7.项目定制
> 修改my_app/my_static为项目名称，并做全文替换my_static为新名称,settings.py里的debug=True
> 修改settings文件里的数据库配置
> 修改my_app/urls.py里的my_api为项目api
> 修改settings.py里的SECRET_KEY
> import random
> ''.join([random.choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)])

---
# 8.新建项目后的检查清单
> 按顺序过一遍，前 3 条是历史遗留的"开箱即炸"项，模板已修复，派生项目若从旧版本拷贝需自查：

1. `my_project/urls.py` 里不要留未 import 的视图引用（曾出现过 `asyncViews` / `celeryViews` 直接写进 urlpatterns）
2. 全文搜索 `my_project.my_app` / `my_project.my_project`，这类错误 import 前缀会让服务起不来
3. `my_project/customPageNumberPagination.py` 必须是真正的分页类
   （`settings.REST_FRAMEWORK.DEFAULT_PAGINATION_CLASS` 指向它，缺失则所有默认分页接口报错）
4. `my_app/models.py` 里 `managed = False` 的模型不要写 `app_label`（指到不存在的 app 会让 `manage.py check` 失败）
5. `settings.py` 里 `DEBUG` 只定义一次
6. 项目级业务常量统一提到 settings（参考 `PAGE_MAX_SIZE` / `REC_MAX_BYTES`），不要散落在 manager 里

## 8.1 使用"忘记密码"功能需要数据库满足
> `auth_user` 表需有 `userpass_question` / `userpass_answer` 两列（模型里未声明这两列，
> 由 `SysmanHelper.retrieve_password` 直接 SQL 读取，避免影响已有库）
> 需新建 `tt_userpass_question`（密保问题字典）和 `tt_retrivepass_token`（一次性重置令牌）两张表
> 不需要该功能时，删掉 `my_app/urls.py` 里的 `ttUserpassQuestion` 路由和 userViews 里对应的 action 即可

## 8.2 多语言提示语的新增约定与自检
> `localization_enum.py` 里每条提示必须是 `<KEY>_CH` / `<KEY>_EN` 成对出现，
> 缺一个就会在运行期 `AttributeError`。
> 新增提示语后跑一次自检脚本（校验 CH/EN 配对 + 代码引用的 key 是否都已定义）：
> ```
> python my_app/tools/check_localization_keys.py
> ```
> 全部通过时退出码为 0，可接入 CI 或提交前钩子。
>
> 业务代码里取提示语的三种方式：
> - `CommonHelper.get_local_str("KEY", request)` —— ViewSet 里按请求头自动选语言
> - `CommonHelper.get_local_str2("KEY", local)` —— manager 层已拿到 local（CH/EN）时
> - `Result.fail(msg, msg, localization=CommonHelper.get_local_flag(request))` —— 统一响应体

---
# 9.vgis库更新
> pip install --upgrade vgis_utils vgis-office vgis-log vgis-database vgis-code vgis-ai vgis-encrption license_authorize -i https://pypi.python.org/simple/

