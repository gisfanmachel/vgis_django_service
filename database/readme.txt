数据表的id不是自增长，用的雪花ID

SQL:
"id" int8 NOT NULL,

MODEL类：
id = models.BigIntegerField(primary_key=True)