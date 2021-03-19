WORD_POOL_KEY = 'word_pool_check'
NEW_WORD_POOL_KEY = 'new_word_pool_check'
BROKER_URL = 'redis://127.0.0.1:6379/0'
RESULT_BACKEND = 'redis://127.0.0.1:6379/0'
ENABLE_UTC = True
# minio
MINIO_URL = 'storage.mooplab.com'
MINIO_ACCESS = 'moop'
MINIO_SECRET = 'd2VsY29tZTEK'
MINIO_SECURE = True
MINIO_BUCKET = 'tibetdictdev'

NOTIFY_URL = "http://127.0.0.1:5555/api/work/notify"
NOTIFY_KEY = "welcome1"

REDIS_CONF = {  # 生产系统使用
    "HOST": "127.0.0.1",
    "PORT": 6379,
    "AUTH": False,  # AUTH 为 True 时需要进行 用户认证
    "PASSWORD": "",
    "DECODE_RESPONSES": True  # 是否对查询结果进行编码处理
}

# mongodb 数据库
MONGODB_CONF = {  # 生产系统使用
    "URL": "192.168.0.61:37017",  # 有此项则优先用此项进行数据库连接
    # 否则用 HOST 和 PORT 连接
    "HOST": "127.0.0.1",
    "PORT": 27017,
    "AUTH": False,  # AUTH 为 True 时需要进行 用户认证
    "USERNAME": "",
    "PASSWORD": "",
    "DEFAULT_DB": "tibetan"  # 默认数据库
}

DEL_CONTENT = ['-', '_', 'x', 'X', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',' ']
