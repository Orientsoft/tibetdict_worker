from celery import Celery
from config import BROKER_URL,RESULT_BACKEND

celery_app = Celery()


class Config:
    broker_url = BROKER_URL
    result_backend = RESULT_BACKEND


celery_app.config_from_object(Config)


if __name__ == '__main__':
    # task = celery_app.send_task('worker:origin_stat', args=['0d9af3a871b711eb964f080027ce4314'], queue='tibetan',
    #                             routing_key='tibetan')
    # print(task)
    import re,time,string
    from flashtext import KeywordProcessor
    header_re = "[ |\]|་|།]"
    footer_re = "[འི|འུ|འོ|ས|ར]?[་|།]"
    word = "བཅོམ་ལྡན་འདས"
    start = time.time()
    p = re.compile(f"{header_re}{word}{footer_re}")
    print(time.time()-start)
    with open('./test.txt','r') as f:
        source = f.read()
    print(time.time()-start)
    # case 1  1.2s
    # kp = KeywordProcessor()
    # kp.set_non_word_boundaries(set(string.digits))
    # kp.add_keyword(word)
    # tmp_found = kp.extract_keywords(source, span_info=True)
    # case 2  0.02s
    # for m in p.finditer(source):
    #     pass
    #     print(m.start()+1,m.start()+1+len(word), m.group())
    # case 3 0.007s
    _offset = 0

    while True:

        _begin = source.find(word, _offset)
        print(_begin)

        if _begin > -1:
            _offset = _begin + len(word)
        else:
            break
    print(time.time()-start)