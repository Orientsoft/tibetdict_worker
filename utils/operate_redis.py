#!/usr/bin/env python3
# -*- coding:utf-8 -*-

'''
@File :  operate_redis.py
@Desc :  操作 Redis 数据库
'''

# Standard library imports
import threading
# Third party imports
import redis
# Local application imports
from config import REDIS_CONF


class OperateRedis:
    """
    操作 Redis 数据库
    """
    _instance_lock = threading.Lock()

    def __init__(self):
        self.REDIS_CONFIG = REDIS_CONF

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            with OperateRedis._instance_lock:
                if not hasattr(cls, '_instance'):
                    OperateRedis._instance = super().__new__(cls)
        return OperateRedis._instance

    def conn_redis(self):
        """
        连接 Redis 数据库
            @return:
                redis_connection
        """
        if self.REDIS_CONFIG['AUTH'] is True:
            pool = redis.ConnectionPool(
                host=self.REDIS_CONFIG['HOST'],
                port=self.REDIS_CONFIG['PORT'],
                password=self.REDIS_CONFIG['PASSWORD'],
                decode_responses=self.REDIS_CONFIG['DECODE_RESPONSES']
            )
        else:
            pool = redis.ConnectionPool(
                host=self.REDIS_CONFIG['HOST'],
                port=self.REDIS_CONFIG['PORT'],
                decode_responses=self.REDIS_CONFIG['DECODE_RESPONSES']
            )
        conn = redis.Redis(connection_pool=pool)
        return conn