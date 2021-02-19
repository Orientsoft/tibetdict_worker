from celery import Celery
import json
from celery.result import AsyncResult, allow_join_result
from kombu import Queue
from config import BROKER_URL, RESULT_BACKEND, ENABLE_UTC, WORD_POOL_KEY

from utils.operate_mongo import OperateMongodb
from utils.operate_redis import OperateRedis
from utils.minio_tools import MinioUploadPrivate
from origin_unit_word import UnitStat
from word_count import WordCount, WordCountError
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
    rd = OperateRedis().conn_redis()
    data = db['work_history'].find_one({'id': work_id})
    m = MinioUploadPrivate()
    origin = m.get_object(data['origin'])
    cache = rd.get(WORD_POOL_KEY)
    if not cache:
        word_pool = db['word_stat_dict'].find({'type': 'stat', 'is_exclude': False})
        result = []

        # 不参与排序
        _link = ['འི་', 'འི།', 'འུ་', 'འུ།', 'འོ་', 'འོ།']
        _tmp_result = []

        for item in word_pool:
            _key = item['word'].strip()
            _value = item['nature'].strip()
            _id = item['id']

            # 如果末尾不为་   , 末尾则加上་
            _tt = _key.split('་')
            _length = len(_tt) - 1

            if _tt[-1] != '':
                _length = _length + 1
                _key = "%s་" % _key

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
        rd.set(WORD_POOL_KEY, json.dumps(save_result, ensure_ascii=False), 3600)
    else:
        word_pool = json.loads(cache)

    u = UnitStat(word_pool)
    if data['work_type'] == 'stat':
        result, tmp_text = u.run(origin.decode('utf-8'))
        # notify request
        notify_result(work_id=work_id, result=result, context=tmp_text, calc_type='origin')
    elif data['work_type'] == 'new':
        pass
    else:
        return


# 分词后文件，计算
@app.task(name='worker:parsed_calc')
def parsed_calc(work_id: str):
    _, db = OperateMongodb().conn_mongodb()
    data = db['work_history'].find_one({'id': work_id})
    try:
        if data['work_type'] == 'stat':
            # todo 调用算法
            result, tmp_text = WordCount(conn=db).word_count(_id=work_id)
            notify_result(work_id=work_id, result=result, context=tmp_text, calc_type='parsed')
        elif data['work_type'] == 'new':
            # todo 调用算法
            result, tmp_text = WordCount(conn=db).new_word(_id=work_id)
            notify_result(work_id=work_id, result=result, context=tmp_text, calc_type='parsed', is_save_to_dict=True)
        else:
            return
    except WordCountError as e:
        print(e.msg)
        return
