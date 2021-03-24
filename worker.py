from celery import Celery
import json
from celery.result import AsyncResult, allow_join_result
from kombu import Queue
from config import BROKER_URL, RESULT_BACKEND, ENABLE_UTC, WORD_POOL_KEY, NEW_WORD_POOL_KEY, DEL_CONTENT

from utils.operate_mongo import OperateMongodb
from utils.operate_redis import OperateRedis
from utils.minio_tools import MinioUploadPrivate
from origin_unit_word import UnitStat
from new_word import NewWord
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


def get_stat_pool(db):
    word_pool = db['word_stat_dict'].aggregate([{'$match': {'type': 'stat', 'is_exclude': False}},
                                                {'$project': {'_id': 0, 'id': 1, 'word': 1, 'nature': 1,
                                                              'length': {'$strLenCP': "$word"}}},
                                                {'$sort': {'length': -1}}
                                                ], allowDiskUse=True)
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
    return word_pool


def get_used_pool(db):
    word_dict_list = [x['word'] for x in db['word_stat_dict'].find({'type': 'used'})]
    # 加入已经确认的新词
    for x in db['self_dict'].find({'is_check': True}):
        word_dict_list.append(x['word'])
    return word_dict_list


# 原始文件计算
@app.task(name='worker:origin_calc')
def origin_calc(work_id: str):
    _, db = OperateMongodb().conn_mongodb()
    data = db['work_history'].find_one({'id': work_id})
    m = MinioUploadPrivate()
    origin = m.get_object(data['origin'])
    pool_key = WORD_POOL_KEY if data['work_type'] == 'stat' else NEW_WORD_POOL_KEY
    rd = OperateRedis().conn_redis()
    cache = rd.get(pool_key)
    if not cache:
        word_pool = get_stat_pool(db) if data['work_type'] == 'stat' else get_used_pool(db)
        rd.set(pool_key, json.dumps(word_pool, ensure_ascii=False), 3600 * 3600)
    else:
        word_pool = json.loads(cache)

    if data['work_type'] == 'stat':
        u = UnitStat(word_pool)
        result, tmp_text = u.run(origin.decode('utf-8'), DEL_CONTENT)
        print(result,tmp_text)
        # notify request
        notify_result(work_id=work_id, result=result, context=tmp_text, calc_type='origin')
    elif data['work_type'] == 'new':
        n = NewWord(word_pool)
        try:
            result = n.run(origin.decode('utf-8'), DEL_CONTENT)
        except:
            result = []
        # notify request
        notify_result(work_id=work_id, result=result, context='', calc_type='origin', is_save_to_dict=True)
    else:
        return


# if __name__ == '__main__':
#     origin_calc('46c9f550870811eba1d9080027ce4314')
