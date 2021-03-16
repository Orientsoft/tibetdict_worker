from celery import Celery
import json
from celery.result import AsyncResult, allow_join_result
from kombu import Queue
from config import BROKER_URL, RESULT_BACKEND, ENABLE_UTC, WORD_POOL_KEY, NEW_WORD_POOL_KEY

from utils.operate_mongo import OperateMongodb
from utils.operate_redis import OperateRedis
from utils.minio_tools import MinioUploadPrivate
from origin_unit_word import UnitStat
from new_word import new_word
from notify import notify_result

app = Celery()


class Config:
    broker_url = BROKER_URL
    result_backend = RESULT_BACKEND
    enable_utc = ENABLE_UTC


app.config_from_object(Config)

app.conf.task_queues = (
    Queue('tibetan', routing_key='tibetan'),
)


# 原始文件计算
@app.task(name='worker:origin_calc')
def origin_calc(work_id: str):
    _, db = OperateMongodb().conn_mongodb()
    data = db['work_history'].find_one({'id': work_id})
    m = MinioUploadPrivate()
    origin = m.get_object(data['origin'])
    if data['work_type'] == 'stat':
        rd = OperateRedis().conn_redis()
        pool_key = WORD_POOL_KEY if data['work_type'] == 'stat' else NEW_WORD_POOL_KEY
        _type = 'stat' if data['work_type'] == 'stat' else 'used'
        cache = rd.get(pool_key)
        if not cache:
            word_pool = db['word_stat_dict'].aggregate([{'$match': {'type': _type, 'is_exclude': False}},
                                                        {'$project': {'_id': 0, 'id': 1, 'word': 1, 'nature': 1,
                                                                      'length': {'$strLenCP': "$word"}}},
                                                        {'$sort': {'length': -1}}
                                                        ], {'allowDiskUse': True})
            result = []

            # 不参与排序
            _link = ['འི་', 'འི།', 'འུ་', 'འུ།', 'འོ་', 'འོ།']
            _tmp_result = []

            for item in word_pool:
                _key = item['word'].strip()
                _value = item['nature'].strip()
                _id = item['id']

                # 如果末尾不为་   , 末尾则加上་
                if not _key.endswith('་'):
                    _key = f'{_key}་'

                if _key in _link:
                    _tmp_result.append({
                        'id': _id,
                        'word': _key,
                        'nature': _value
                    })
                else:
                    result.append({
                        'id': _id,
                        'word': _key,
                        'nature': _value
                    })
            save_result = result + _tmp_result
            word_pool = save_result
            rd.set(pool_key, json.dumps(save_result, ensure_ascii=False), 3600)
        else:
            word_pool = json.loads(cache)
        u = UnitStat(word_pool)
        result, tmp_text = u.run(origin.decode('utf-8'))
        # notify request
        notify_result(work_id=work_id, result=result, context=tmp_text, calc_type='origin')
    elif data['work_type'] == 'new':
        result = new_word(db=db, source=origin.decode('utf-8'))
        # notify request
        notify_result(work_id=work_id, result=result, context='', calc_type='origin', is_save_to_dict=True)
    else:
        return


# 分词后文件，计算
# @app.task(name='worker:parsed_calc')
# def parsed_calc(work_id: str):
#     _, db = OperateMongodb().conn_mongodb()
#     data = db['work_history'].find_one({'id': work_id})
#     try:
#         if data['work_type'] == 'stat':
#             result, tmp_text = WordCount(conn=db).word_count(_id=work_id)
#             notify_result(work_id=work_id, result=result, context=tmp_text, calc_type='parsed')
#         elif data['work_type'] == 'new':
#             result, tmp_text = WordCount(conn=db).new_word(_id=work_id)
#             notify_result(work_id=work_id, result=result, context=tmp_text, calc_type='parsed', is_save_to_dict=True)
#         else:
#             return
#     except WordCountError as e:
#         print(e.msg)
#         return
